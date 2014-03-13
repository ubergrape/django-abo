import logging
import pymill
from datetime import datetime

from django import forms
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError

from abo.signals import payment_error
from abo import get_subscription_model, get_plan_model
from abo.models import BackendPayment, BackendPlan, BackendSubscription, BackendClient

from . import PaymentProcessor


Plan = get_plan_model()
Subscription = get_subscription_model()

logger = logging.getLogger(__name__)


class PaymillForm(forms.Form):
    token = forms.CharField(widget=forms.HiddenInput())
    plan = forms.ModelChoiceField(queryset=Plan.objects.all())
    quantity = forms.IntegerField()
    email = forms.EmailField(help_text=_('Receipts will be sent to this email address'))

    def __init__(self, *args, **kwargs):
        self.Pymill = pymill.Pymill
        return super(PaymillForm, self).__init__(*args, **kwargs)

    def set_pymill(self, pymill_class):
        '''IoC for testings'''
        self.Pymill = pymill_class

    def raise_paymill_validation_error(self, exception):
        if len(exception.args) and type(exception.args[0]) == dict:
            error_code = exception.args[0].get('exception', 'error')
            error_message = exception.args[0].get('error', 'Error')
        else:
            error_code = 'error'
            error_message = 'Error'

        payment_error.send(sender=self, error_code=error_code, exception=exception)

        # TODO: notify developers
        raise ValidationError(_("Payment failed. Our developers have been notified."), code=error_code)

    def clean(self):
        cleaned_data = super(PaymillForm, self).clean()

        token = cleaned_data.get('token')
        plan = cleaned_data.get('plan')
        quantity = cleaned_data.get('quantity')
        email = cleaned_data.get('email')

        if not token or not plan or not quantity or not email:
            return cleaned_data

        self.subscription = None

        paymill = self.Pymill(PaymentProcessor.get_backend_setting('PAYMILL_PRIVATE_KEY'))

        self.backend = PaymentProcessor.BACKEND

        logger.debug('create client and save to DB')

        try:
            client = paymill.new_client(email=email)
        except Exception as e:
            self.raise_paymill_validation_error(e)

        backend_client = BackendClient.objects.create(
            backend=self.backend,
            external_id=client.id,
            created_at=client.created_at,
            email=email
        )

        logger.debug('create payment (card/direct debit) and save to DB')

        try:
            # new_card() also works for direct debit
            payment = paymill.new_card(token=token, client=backend_client.external_id)
        except Exception as e:
            self.raise_paymill_validation_error(e)

        backend_payment = BackendPayment.objects.create(
            backend=self.backend,
            external_id=payment.id,
            client=backend_client,
            payment_type=payment.type,
            card_type=payment.card_type,
            holder=payment.card_holder or payment.holder,  # cc --> card_holder; dd --> holder
            expire_month=payment.expire_month,
            expire_year=payment.expire_year,
            last4=payment.last4,
            code=payment.code,
            account=payment.account,
            iban=payment.iban,
            bic=payment.bic,
            created_at=payment.created_at
            # updated_at=payment.updated_at
        )

        backend_plan = BackendPlan.objects.filter(
            backend=self.backend,
            plan=plan,
            quantity=quantity
        )

        if not backend_plan.exists():
            logger.debug('create offer on paymill and save it to DB')

            amount = plan.amount * quantity
            interval = "{} {}".format(
                plan.interval_count or 1,
                plan.interval)
            name = "{}, Quantity: {}".format(
                plan.name,
                quantity)

            try:
                offer = paymill.new_offer(
                    amount=amount,
                    interval=interval,
                    name=name,
                    currency='EUR'
                )
            except Exception as e:
                self.raise_paymill_validation_error(e)

            subscription_count = getattr(offer, 'subscription_count', {'active': None, 'inactive': None})

            backend_plan = BackendPlan.objects.create(
                backend=self.backend,
                external_id=offer.id,
                plan=plan,
                quantity=quantity,
                subscription_count_active=subscription_count.get('active'),
                subscription_count_inactive=subscription_count.get('inactive'),
                created_at=getattr(offer, 'created_at', datetime.now()),
                updated_at=getattr(offer, 'updated_at', datetime.now())
            )
        else:
            logger.debug('offer already created, using it')
            backend_plan = backend_plan[0]

        logger.debug('create subscription')

        self.subscription = Subscription.objects.create(
            plan=plan,
            quantity=quantity,
            currency='EUR',
            # LOL APP SPECIFIC FIELD!!?!?!
        )

        logger.debug('subscribe!')

        try:
            subscription = paymill.new_subscription(
                client=backend_client.external_id,
                offer=backend_plan.external_id,
                payment=backend_payment.external_id
            )
        except Exception as e:
            self.raise_paymill_validation_error(e)

        BackendSubscription.objects.create(
            backend=self.backend,
            external_id=subscription.id,
            subscription=self.subscription,
            backend_plan=backend_plan,
            backend_payment=backend_payment,
            client=backend_client,
            status='new',
            created_at=subscription.created_at,
            updated_at=subscription.updated_at,
            # next_capture_at=subscription.next_capture_at, # TODO
            # canceled_at=subscription.canceled_at # TODO
        )

        logger.info("successfuly subscribed %s to %s" % (backend_client, self.subscription))

        return cleaned_data
