from django.utils.translation import ugettext_lazy as _

from .utils import get_backend_choices


BACKEND_CHOICES = get_backend_choices()

SUBSCRIPTION_STATUS_CHOICES = (
    ('new', _('new')),
    ('in_progress', _('in progress')),
    ('partially_paid', _('partially paid')),
    ('paid', _('paid')),
    ('failed', _('failed')),
)

TRANSACTION_STATUS_CHOICES = (
    ('open', _('open')),
    ('pending', _('pending')),
    ('closed', _('closed')),
    ('failed', _('failed')),
    ('partial_refunded', _('partial_refunded')),
    ('refunded', _('refunded')),
    ('preauthorize', _('preauthorize')),
    ('chargeback', _('chargeback')),
)


PLAN_INTERVAL_CHOICES = (
    ('year', _('year')),
    ('month', _('month')),
    ('week', _('week')),
    ('day', _('day')),
)

PLAN_TYPE_CHOICES = (
    ('fixed', _('fixed')),
    ('per_user', _('per_user')),
)
