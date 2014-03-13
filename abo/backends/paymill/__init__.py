from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from abo.backends import PaymentProcessorBase

default_app_config = 'abo.backends.paymill.apps.PaymillConfig'


class PaymentProcessor(PaymentProcessorBase):
    BACKEND = 'abo.backends.paymill'
    BACKEND_NAME = _('Paymill')
    BACKEND_ACCEPTED_CURRENCY = ('EUR', 'CZK', 'DKK', 'HUF', 'ISK', 'ILS',
                                 'LVL', 'CHF', 'NOK', 'PLN', 'SEK', 'TRY',
                                 'GBP', )

    @classmethod
    def get_gateway_url(cls, request):
        return reverse('abo-paymill-authorization'), "GET", {}
