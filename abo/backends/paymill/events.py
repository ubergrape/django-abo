from abo.models import BackendSubscription
from .webhooks import WEBHOOK_EVENTS


class EventProcessor():
    """
    Handle the paymill events we received through a webhook

    This will be used by BackendEvent.process()
    """

    def __init__(self, backend_event):
        self.backend_event = backend_event
        self.object = None

    def process(self):
        # TODO also handle errors in message
        event = self.backend_event.message.get('event')

        if not self.backend_event.event_type in WEBHOOK_EVENTS:
            raise NotImplementedError(self.backend_event.event_type)

        event_fn_name = self.backend_event.event_type.replace('.', '_')
        event_fn = getattr(self, "_" + event_fn_name, None)

        if event_fn:
            event_fn(event)

        if self.object:
            self.object.save()

    def _chargeback_executed(self, event):
        raise NotImplementedError()

    def _refund_created(self, event):
        raise NotImplementedError()

    def _refund_succeeded(self, event):
        raise NotImplementedError()

    def _refund_failed(self, event):
        raise NotImplementedError()

    def _subscription_created(self, event):
        self.object = BackendSubscription.objects.get(external_id=event['event_resource']['subscription']['id'])
        self.backend_event.content_object = self.object
        self.object.status = 'in_progress'

    def _subscription_updated(self, event):
        raise NotImplementedError()

    def _subscription_deleted(self, event):
        self.object.subscription.deleted = True
        self.object.subscription.save()
        self.object.canceled_at = event['event_resource']['subscription']['canceled_at']

    def _subscription_succeeded(self, event):
        self._subscription_created(event)
        self.object.status = 'paid'

    def _subscription_failed(self, event):
        self._subscription_created(event)
        self.object.status = 'failed'

    def _transaction_created(self, event):
        raise NotImplementedError()

    def _transaction_succeeded(self, event):
        raise NotImplementedError()

    def _transaction_failed(self, event):
        raise NotImplementedError()

    def _invoice_available(self, event):
        raise NotImplementedError()

    def _payout_transferred(self, event):
        raise NotImplementedError()

    def _app_merchant_activated(self, event):
        raise NotImplementedError()

    def _app_merchant_deactivated(self, event):
        raise NotImplementedError()

    def _app_merchant_rejected(self, event):
        raise NotImplementedError()

    def _client_updated(self, event):
        raise NotImplementedError()

    def _app_merchant_app_disabled(self, event):
        raise NotImplementedError()
