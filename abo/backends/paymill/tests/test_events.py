import json

from django.test import TestCase
from django.core.urlresolvers import reverse

from abo.factories import PlanFactory
from abo.backends.paymill.forms import PaymillForm
from abo.models import BackendSubscription

from .mockups import Mockmill


class EventTestCase(TestCase):
    def _create_subscription(self):
        self.plan = PlanFactory()
        self.formdata = {
            'token': 'xxx123',
            'plan': self.plan.id,
            'quantity': 1,
            'email': 'test@example.com'
        }
        form = PaymillForm(data=self.formdata)
        form.set_pymill(Mockmill)
        form.full_clean()

    def setUp(self):
        self._create_subscription()
        self.secret = "0" * 32
        self.webhook_url = reverse('abo-paymill-webhook', args=[self.secret, ])

    def test_successful_subscription(self):
        msg = {u'event': {u'event_resource': {u'transaction': {u'status': u'closed', u'created_at': 1393435183, u'description': u'Subscription#subscription1 Almost Free Extended 50% off, Quantity: 3', u'refunds': None, u'invoices': [], u'response_code': 20000, u'livemode': False, u'origin_amount': 110094, u'updated_at': 1393435184, u'preauthorization': None, u'app_id': None, u'currency': u'EUR', u'amount': u'110094', u'short_id': u'7357.7357.7357', u'client': {u'description': None, u'payment': [u'payment1'], u'created_at': 1393435182, u'updated_at': 1393435182, u'app_id': None, u'id': u'client1', u'email': u'admin@chatgrape.com', u'subscription': None}, u'fees': [], u'id': u'transaction1', u'is_fraud': False, u'payment': {u'expire_month': u'11', u'country': None, u'created_at': 1393435181, u'app_id': None, u'updated_at': 1393435183, u'card_type': u'mastercard', u'last4': u'0004', u'client': u'client1', u'type': u'creditcard', u'expire_year': u'2020', u'card_holder': u'l\xf6kasdf', u'id': u'payment1'}}, u'subscription': {u'trial_start': None, u'cancel_at_period_end': False, u'offer': {u'subscription_count': {u'active': u'1', u'inactive': 0}, u'name': u'Almost Free Extended 50% off, Quantity: 3', u'created_at': 1393435183, u'interval': u'3 YEAR', u'app_id': None, u'updated_at': 1393435183, u'currency': u'EUR', u'amount': 110094, u'trial_period_days': 0, u'id': u'offer1'}, u'canceled_at': None, u'created_at': 1393435183, u'livemode': False, u'updated_at': 1393435184, u'app_id': None, u'trial_end': None, u'client': {u'description': None, u'payment': [{u'expire_month': u'11', u'country': None, u'created_at': 1393435181, u'app_id': None, u'updated_at': 1393435183, u'card_type': u'mastercard', u'last4': u'0004', u'client': u'client1', u'type': u'creditcard', u'expire_year': u'2020', u'card_holder': u'l\xf6kasdf', u'id': u'payment1'}], u'created_at': 1393435182, u'updated_at': 1393435182, u'app_id': None, u'id': u'client1', u'email': u'admin@chatgrape.com', u'subscription': None}, u'next_capture_at': 1488129584, u'id': u'subscription1', u'payment': {u'expire_month': u'11', u'country': None, u'created_at': 1393435181, u'app_id': None, u'updated_at': 1393435183, u'card_type': u'mastercard', u'last4': u'0004', u'client': u'client1', u'type': u'creditcard', u'expire_year': u'2020', u'card_holder': u'l\xf6kasdf', u'id': u'payment1'}}}, u'created_at': 1393435184, u'event_type': u'subscription.succeeded', u'app_id': None}}

        self.client.post(self.webhook_url, json.dumps(msg), content_type="application/json")

        bs = BackendSubscription.objects.get(external_id='subscription1')
        self.assertEqual(bs.status, 'paid')

    def test_failed_subscription(self):
        msg = {u'event': {u'event_resource': {u'transaction': {u'status': u'failed', u'created_at': 1393529473, u'description': u'Subscription#subscription1 Product Extended 50% off, Quantity: 5', u'refunds': None, u'invoices': [], u'response_code': 40103, u'livemode': False, u'origin_amount': 16905, u'updated_at': 1393529473, u'preauthorization': None, u'app_id': None, u'currency': u'EUR', u'amount': u'16905', u'short_id': None, u'client': {u'description': None, u'payment': [u'payment1'], u'created_at': 1393529473, u'updated_at': 1393529473, u'app_id': None, u'id': u'client1', u'email': u'admin@chatgrape.com', u'subscription': None}, u'fees': [], u'id': u'transaction1', u'is_fraud': False, u'payment': {u'expire_month': u'4', u'country': None, u'created_at': 1393529472, u'app_id': None, u'updated_at': 1393529473, u'card_type': u'mastercard', u'last4': u'5100', u'client': u'client1', u'type': u'creditcard', u'expire_year': u'2020', u'card_holder': u'lol rofl', u'id': u'payment1'}}, u'subscription': {u'trial_start': None, u'cancel_at_period_end': False, u'offer': {u'subscription_count': {u'active': u'2', u'inactive': 0}, u'name': u'Product Extended 50% off, Quantity: 5', u'created_at': 1393529369, u'interval': u'2 YEAR', u'app_id': None, u'updated_at': 1393529369, u'currency': u'EUR', u'amount': 16905, u'trial_period_days': 0, u'id': u'offer_f056f0ad034952fd8992'}, u'canceled_at': None, u'created_at': 1393529473, u'livemode': False, u'updated_at': 1393529473, u'app_id': None, u'trial_end': None, u'client': {u'description': None, u'payment': [{u'expire_month': u'4', u'country': None, u'created_at': 1393529472, u'app_id': None, u'updated_at': 1393529473, u'card_type': u'mastercard', u'last4': u'5100', u'client': u'client1', u'type': u'creditcard', u'expire_year': u'2020', u'card_holder': u'lol rofl', u'id': u'payment1'}], u'created_at': 1393529473, u'updated_at': 1393529473, u'app_id': None, u'id': u'client1', u'email': u'admin@chatgrape.com', u'subscription': None}, u'next_capture_at': 1456601473, u'id': u'subscription1', u'payment': {u'expire_month': u'4', u'country': None, u'created_at': 1393529472, u'app_id': None, u'updated_at': 1393529473, u'card_type': u'mastercard', u'last4': u'5100', u'client': u'client1', u'type': u'creditcard', u'expire_year': u'2020', u'card_holder': u'lol rofl', u'id': u'payment1'}}}, u'created_at': 1393529473, u'event_type': u'subscription.failed', u'app_id': None}}

        self.client.post(self.webhook_url, json.dumps(msg), content_type="application/json")

        bs = BackendSubscription.objects.get(external_id='subscription1')
        self.assertEqual(bs.status, 'failed')
