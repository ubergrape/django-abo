from django.test import TestCase

from abo.factories import PlanFactory
from abo.backends.paymill.forms import PaymillForm
from abo.models import BackendPayment, BackendPlan, BackendSubscription
from abo import get_subscription_model

from .mockups import Mockmill, MockmillFailOffer

Subscription = get_subscription_model()


class FormHandlingTestCase(TestCase):
    def setUp(self):
        self.plan = PlanFactory()
        self.formdata = {
            'token': 'xxx123',
            'plan': self.plan.id,
            'quantity': 1,
            'email': 'test@example.com'
        }

    def test_failing_paymill_offer(self):
        backend_offer_count_before = BackendPlan.objects.count()

        form = PaymillForm(data=self.formdata)
        form.set_pymill(MockmillFailOffer)
        form.full_clean()

        self.assertEquals(BackendPayment.objects.filter(external_id="payment1").count(), 1)
        self.assertEquals(BackendPlan.objects.count(), backend_offer_count_before)

        # Important: no subscription and backendsubscription have been created
        self.assertEquals(Subscription.objects.count(), 0)
        self.assertEquals(BackendSubscription.objects.count(), 0)

        self.assertTrue('Payment failed. Our developers have been notified.' in form.errors.get('__all__'))

    def test_successful_payment(self):
        form = PaymillForm(data=self.formdata)
        form.set_pymill(Mockmill)
        form.full_clean()

        self.assertEquals(BackendPayment.objects.filter(external_id="payment1").count(), 1)
        self.assertEquals(BackendPlan.objects.filter(external_id="offer1").count(), 1)
        self.assertEquals(BackendSubscription.objects.filter(external_id="subscription1").count(), 1)

        self.assertEquals(form.subscription, BackendSubscription.objects.get(external_id="subscription1").subscription)
        self.assertEquals(form.subscription.plan, BackendPlan.objects.get(external_id="offer1").plan)
