import json
import uuid
import logging

from django.http import HttpResponse, HttpResponseBadRequest
from django.core.urlresolvers import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import FormView

from . import PaymentProcessor
from .forms import PaymillForm

from abo.models import BackendEvent

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def webhook(request, secret):
    # TODO: compare secret

    logger.debug('Message received')

    # TODO: find out backend from request url
    backend = "abo.backends.paymill"
    message = json.loads(request.body)

    # TODO: find out livemode - it's not in the event json
    livemode = False

    logger.debug(message)

    if type(message) != dict or not message.get("event") or type(message["event"]) != dict or not message["event"].get("event_type"):
        logger.warning("no event_type in message")
        return HttpResponseBadRequest()

    backend_event = BackendEvent.objects.create(
        backend=backend,
        external_id=str(uuid.uuid4()),  # paymill provides no id for events
        event_type=message["event"]["event_type"],
        livemode=livemode,
        message=message
    )
    backend_event.process()

    # always return an empty page, HTTP 200
    return HttpResponse()


class PaymillView(FormView):
    form_class = PaymillForm
    template_name = "paymill.html"
    backend = 'abo.backends.paymill'

    def get_context_data(self, **kwargs):
        context = super(PaymillView, self).get_context_data(**kwargs)
        context['PAYMILL_PUBLIC_KEY'] = PaymentProcessor.get_backend_setting('PAYMILL_PUBLIC_KEY')
        return context

    def form_valid(self, form):
        self.subscription = form.subscription
        return super(PaymillView, self).form_valid(form)

    def get_success_url(self):
        return reverse('abo-success', kwargs={'pk': self.subscription.pk})
