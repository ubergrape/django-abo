from datetime import datetime
import pymill
import requests
import json

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model

from abo.factories import PlanFactory
from abo.backends.paymill.forms import PaymillForm
from abo.models import BackendPayment, BackendPlan, BackendSubscription
from abo import get_subscription_model

Subscription = get_subscription_model()
User = get_user_model()


class Mockmill(object):
    def __init__(*args, **kwargs):
        pass

    def new_client(self, *args, **kwargs):
        return pymill.Client(
            id="client1",
            email=kwargs.get('email'),
            created_at=datetime.now()
        )

    def new_card(self, token, client):
        '''return a new card without checking the token'''
        return pymill.Payment(
            id="payment1",
            client=client,
            type="creditcard",
            card_type="mastercard",
            card_holder="hans horst",
            expire_month="01",
            expire_year="2017",
            last_4="1234",
            code="123",
            created_at=datetime.now()
        )

    def new_offer(*args, **kwargs):
        return pymill.Offer(
            id="offer1",
            name="offer1",
            amount=1911,
            interval="1 MONTH",
            trial_perioade_days=None
        )

    def new_subscription(self, *args, **kwargs):
        return pymill.Subscription(
            id="subscription1",
            offer="offer1",
            livemode=False,
            cancel_at_period_end=None,
            canceled_at=None,
            interval="month",
            payment="payment1",
            client="client1",
            next_capture_at=datetime.now(),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )


class MockmillFailOffer(Mockmill):
    def new_offer(*args, **kwargs):
        json_data = {'exception': 'mocked exception', 'error': 'something went wrong'}
        raise Exception(json_data)


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


class IntegrationTestcase(TestCase):
    '''
    This tests the url config and the view (not only the form) using
    the real paymill testing backend.
    So this should completely test the payment, except for the frontend
    '''

    def setUp(self):
        self.plan = PlanFactory()
        self.user = User.objects.create_user('test', 'test@example.com', 'testpassword')
        self.client.login(username='test', password='testpassword')
        self.assertEqual(self.client.session['_auth_user_id'], self.user.pk)
        self.formdata = {
            'token': 'xxx123',
            'plan': self.plan.id,
            'quantity': 1,
            'email': 'test@example.com'
        }
        self.paymilldata = {
            'transaction.mode': 'CONNECTOR_TEST',
            'channel.id': '611273627719438339e4f177bcd9415c',
            'response.url': 'https://test-tds.paymill.de/end.php?parentUrl=http%253A%252F%252Flocalhost%253A8000%252Fpayment%252Fpaymill%252Fsubscribe%252F&',
            'jsonPFunction': 'window.paymill.transport.paymillCallback4002331054',
            'account.number': '4111111111111111',
            'account.expiry.month': '01',
            'account.expiry.year': '2021',
            'account.verification': '123',
            'account.holder': 'Test Test'
        }

    def test_html_contains_token_input(self):
        response = self.client.post(
            reverse('abo-paymill-authorization'),
            {'text': ''})

        token_input = '<input id="id_token" name="token" type="hidden" />'

        self.assertInHTML(token_input, response.content)

    def test_fake_token(self):
        response = self.client.post(
            reverse('abo-paymill-authorization'), self.formdata)

        # assertFormError has to be fixed in django
        # self.assertFormError(response, form='PaymillForm', field='__all__', errors="Token not Found")
        form = response.context[0].get('form')

        # Important: no subscription and backendsubscription have been created
        self.assertEquals(Subscription.objects.count(), 0)
        self.assertEquals(BackendSubscription.objects.count(), 0)

        self.assertTrue('Payment failed. Our developers have been notified.' in form.errors.get('__all__'))

    def test_fake_plan(self):
        self.formdata['plan'] = 'xxxx'
        response = self.client.post(
            reverse('abo-paymill-authorization'), self.formdata)
        form = response.context[0].get('form')

        # Important: no subscription and backendsubscription have been created
        self.assertEquals(Subscription.objects.count(), 0)
        self.assertEquals(BackendSubscription.objects.count(), 0)

        self.assertTrue('Select a valid choice. That choice is not one of the available choices.' in form.errors.get('plan'))

    def test_successful_payment(self):
        # request token from paymill test API. this is usually done in the
        # frontend with JS, but this is not a frontend test

        r1 = requests.get('https://test-token.paymill.de/', params=self.paymilldata)

        # ugly: strip away JS callback function and parse to json

        r1_cleaned = r1.text[r1.text.index('(') + 1:-1]
        r1_json = json.loads(r1_cleaned)

        # check if our request was processed and if we got a token

        self.assertEquals(r1_json['transaction']['processing']['result'], 'ACK')
        self.formdata['token'] = r1_json['transaction']['identification']['uniqueId']
        self.assertIn('tok_', self.formdata['token'])

        # now that we have the token, make a request to our own paymill view

        r2 = self.client.post(reverse('abo-paymill-authorization'), self.formdata)

        self.assertIn('/success/', r2.url)


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
