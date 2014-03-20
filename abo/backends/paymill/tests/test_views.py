import requests
import json

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model

from abo.factories import PlanFactory
from abo.models import BackendSubscription
from abo import get_subscription_model

Subscription = get_subscription_model()
User = get_user_model()


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
