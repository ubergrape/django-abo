# -*- coding: utf-8 -*-

import logging

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType

from . import settings, signals
from .utils import import_name
from .fields import JSONField
from .choices import *

logger = logging.getLogger(__name__)


class AbstractPlan(models.Model):
    """
    Represents a plan a customer can subscribe to.

    This should be subclassed; the subclass should be registered as
    PLAN_MODEL in the settings.
    """
    name = models.CharField(max_length=512)
    amount = models.IntegerField(_('amount in cents'))
    interval = models.CharField(max_length=10, choices=PLAN_INTERVAL_CHOICES)
    interval_count = models.SmallIntegerField()
    trial_period_days = models.IntegerField(null=True)
    visible = models.BooleanField(_('visible'), default=True)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True, db_index=True)

    class Meta:
        abstract = True

    def __unicode__(self):
        return "%s: %.2f/%s %s" % (self.name, self.amount / 100, self.interval_count, self.interval)


class Plan(AbstractPlan):
    """ Default Plan Model. If you want to change this, check out AbstractPlan """
    class Meta(AbstractPlan.Meta):
        swappable = 'PLAN_MODEL'


class AbstractSubscription(models.Model):
    """
    Represents a subscription, created when a customer subscribes to a plan.

    This should be subclassed; the subclass should be registered as
    SUBSCRIPTION_MODEL in the settings
    """
    plan = models.ForeignKey(settings.PLAN_MODEL, verbose_name=_('Plan'))
    quantity = models.IntegerField()
    total = models.DecimalField(decimal_places=2, max_digits=8, default=0)
    currency = models.CharField(max_length=3, default='EUR')
    deleted = models.BooleanField(default=False)
    #TODO: generic foreign key "subscriber"

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        subscription = super(AbstractSubscription, self).__init__(*args, **kwargs)
        signals.new_subscription.send(sender=None, subscription=subscription)
        return subscription

    def __unicode__(self):
        return "%s x '%s', %.2f %s" % (self.quantity, self.plan, self.total, self.currency)

    def save(self, *args, **kwargs):
        self.total = self.quantity * self.plan.amount / 100
        return super(AbstractSubscription, self).save(*args, **kwargs)


class Subscription(AbstractSubscription):
    """ Default Subscription Model. If you want to change this, check out AbstractSubscription """
    class Meta(AbstractSubscription.Meta):
        swappable = 'SUBSCRIPTION_MODEL'


class BackendModel(models.Model):
    """
    All Models that save backend specific information (BackendPlan, BackendSubscription) always need to save the id the payment gateway created for the object and the creation time.
        """
    backend = models.CharField(_("backend"), max_length=50, choices=BACKEND_CHOICES)
    external_id = models.CharField(max_length=64)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True, db_index=True)

    class Meta:
        abstract = True


class BackendPayment(BackendModel):
    client = models.ForeignKey('BackendClient', null=True)
    payment_type = models.CharField(_("payment type"), max_length=50)
    message = JSONField()
    livemode = models.BooleanField(default=False)
    updated_at = models.DateTimeField(_("updated_at"), auto_now_add=True)
    holder = models.CharField(_("account holder"), max_length=200, blank=True, null=True)

    # for credit cards only
    expire_month = models.PositiveSmallIntegerField(_("expire month"), blank=True, null=True)
    expire_year = models.PositiveSmallIntegerField(_("expire year"), blank=True, null=True)
    last4 = models.CharField(_("last four digits"), max_length=4, blank=True, null=True)
    card_type = models.CharField(_("card type"), max_length=50, blank=True, null=True)

    # for debit accounts only
    code = models.CharField(_("Bank code"), max_length=50, blank=True, null=True)
    account = models.CharField(_("Bank account"), max_length=50, blank=True, null=True)
    iban = models.CharField(_("IBAN"), max_length=50, blank=True, null=True)
    bic = models.CharField(_("BIC"), max_length=50, blank=True, null=True)


class BackendPlan(BackendModel):
    """
    Holds all the information on a plan on a specific backend. A Plan can have multiple BackendPlans, if you use multiple backends or if one backend needs them for internal reasons (see the following comment).

    Comment on field `quantity`: this is needed for backends that don't support to subscribe to a "quantity" of plans.
    Example: You offer a plan for 1€/user/month. A user can subscribe to the plan with 5 users and pay 5€/month. this shouldn't change the plan but only the quantity, saved in the subscription model. Stripe supports this, Paymill doesn't. For Paymill we have to create a seperate BackendPlan for every quantity.
    """
    plan = models.ForeignKey(settings.PLAN_MODEL)
    quantity = models.IntegerField(blank=True, null=True)
    updated_at = models.DateTimeField(_("updated on"), auto_now_add=True)
    subscription_count_active = models.IntegerField(_("active subscribers"), null=True)
    subscription_count_inactive = models.IntegerField(_("inactive subscribers"), null=True)


class BackendSubscription(BackendModel):
    """
    Holds all the information on a subscription on a specific backend. A BackendSubscription is always connected to a single BackendPlan from the same backend.
    """
    subscription = models.ForeignKey(settings.SUBSCRIPTION_MODEL)
    backend_plan = models.ForeignKey(BackendPlan)
    backend_payment = models.ForeignKey(BackendPayment)
    client = models.ForeignKey('BackendClient', null=True)
    status = models.CharField(_("status"), max_length=20, choices=SUBSCRIPTION_STATUS_CHOICES, default='new', db_index=True)
    updated_at = models.DateTimeField(_("updated on"), auto_now_add=True)
    next_capture_at = models.DateTimeField(_("next capture on"), null=True)
    canceled_at = models.DateTimeField(_("canceled on"), null=True)

    def get_absolute_url(self):
        return reverse('abo-success',
                       args={'pk': self.pk})


class BackendEvent(BackendModel):
    event_type = models.CharField(max_length=250)
    livemode = models.BooleanField(default=False)
    message = JSONField()
    processed = models.BooleanField(default=False)
    content_type = models.ForeignKey(ContentType, null=True)
    object_id = models.PositiveIntegerField(null=True)
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    def process(self):
        if not self.processed:
            backend = import_name(self.backend + ".events")
            processor = getattr(backend, "EventProcessor")
            processor(self).process()

            self.processed = True
            self.save()


class BackendClient(BackendModel):
    """
    Holds information on a client on a specific backend. The actual payment info is saved in BackendPayment. Paymill needs a client object, but other backends might not.
    """
    email = models.CharField(max_length=300, blank=True, null=True)
    description = models.CharField(max_length=300, blank=True, null=True)
    updated_at = models.DateTimeField(_("updated_at"), auto_now_add=True, db_index=True)

    def __unicode__(self):
        return u"%s (%s)" % (self.email or "No Email", self.backend)

# class BackendTransaction(BackendModel):
#     amount = models.IntegerField(_('amount in cents'))
#     origin_amount = models.IntegerField(_('used amount in cents'))  # other currency
#     currency = models.CharField(max_length=3, default='EUR')
#     status = models.CharField(_("status"), max_length=20, choices=TRANSACTION_STATUS_CHOICES, db_index=True)
#     livemode = models.BooleanField()
#     is_fraud = models.BooleanField()
#     payment = models.ForeignKey(BackendPayment)
#     updated_at = models.DateTimeField(_("updated at"))
#     response_code = models.CharField(_("response code"), max_length=20)
#     short_id = models.CharField(_("short id"), max_length=100)
#     fees = models.TextField(_("fees"))

from abo.signals import payment_error
from django.dispatch import receiver


@receiver(payment_error)
def payment_error_callback(sender, error_code, exception, **kwargs):
    logger.error(error_code)
