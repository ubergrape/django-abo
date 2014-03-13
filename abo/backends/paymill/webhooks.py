import uuid
from urlparse import urlparse
from django.core.urlresolvers import reverse, resolve
from django.core.exceptions import ImproperlyConfigured

import pymill

from . import PaymentProcessor


WEBHOOK_EVENTS = (
    u'chargeback.executed',
    u'refund.created',
    u'refund.succeeded',
    u'refund.failed',
    u'subscription.created',
    u'subscription.updated',
    u'subscription.deleted',
    u'subscription.succeeded',
    u'subscription.failed',
    u'transaction.created',
    u'transaction.succeeded',
    u'transaction.failed',
    u'invoice.available',
    u'payout.transferred',
    u'app.merchant.activated',
    u'app.merchant.deactivated',
    u'app.merchant.rejected',
    u'client.updated',
    u'app.merchant.app.disabled'
)


class Webhook(object):
    def __init__(self, *args, **kwargs):
        self.Pymill = pymill.Pymill
        self.host = PaymentProcessor.get_backend_setting('PAYMILL_WEBHOOK_HOST')
        self.secret = None
        return super(Webhook, self).__init__(*args, **kwargs)

    def set_pymill(self, pymill_class):
        '''IoC for testings'''
        self.Pymill = pymill_class

    def get_webhook(self):
        if self.secret:
            return self.secret

        paymill = self.Pymill(PaymentProcessor.get_backend_setting('PAYMILL_PRIVATE_KEY'))
        webhooks = paymill.get_webhooks()
        host = urlparse(self.host)
        for hook in webhooks:
            url = urlparse(hook.url)
            try:
                match = resolve(url.path)
                if host.scheme == url.scheme and host.netloc == url.netloc and match.url_name == 'abo-paymill-webhook':
                    self.secret = match.kwargs.get('secret', None)
                    return self.secret
            except:
                pass

        return self.secret

    def install_webhook(self):
        paymill = self.Pymill(PaymentProcessor.get_backend_setting('PAYMILL_PRIVATE_KEY'))
        if not self.host:
            raise ImproperlyConfigured('You need to set PAYMILL_WEBHOOK_HOST in your backend settings for paymill')
        secret = uuid.uuid4().hex
        url = '%s%s' % (
            self.host,
            reverse('abo-paymill-webhook', args=[secret, ]))
        print 'Registering webhook: %s' % url
        paymill.new_webhook(url, WEBHOOK_EVENTS)
        self.secret = secret

    def init_webhook(self):
        print 'Looking for webhook'
        secret = self.get_webhook()
        if not secret:
            print 'Webhook not found, installing'
            self.install_webhook()

    def get_url(self):
        if not self.secret:
            self.get_webhook()
        return self.host + reverse('abo-paymill-webhook', args=[self.secret, ])
