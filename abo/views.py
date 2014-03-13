from django.views.generic import TemplateView
from django.views.generic.base import RedirectView


from . import get_plan_model
from .utils import get_default_backend


Plan = get_plan_model()


class PaymentsContextMixin(object):

    def get_context_data(self, **kwargs):
        context = super(PaymentsContextMixin, self).get_context_data(**kwargs)
        context.update({
            "PLAN_CHOICES": Plan.objects.all(),
            "BACKEND": get_default_backend()
        })
        return context


class SubscribeView(RedirectView):

    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        backend = get_default_backend()
        url, _, _ = backend.PaymentProcessor.get_gateway_url(None)
        return url

# class SubscribeView(PaymentsContextMixin, TemplateView):
#     template_name = "subscribe.html"

#     def get_context_data(self, **kwargs):
#         context = super(SubscribeView, self).get_context_data(**kwargs)
#         context.update({
#             "organization": "ubergrape",  # todo
#             "form": PlanForm
#         })
#         return context


class ChangeCardView(PaymentsContextMixin, TemplateView):
    template_name = "change_card.html"


class CancelView(PaymentsContextMixin, TemplateView):
    template_name = "cancel.html"


class ChangePlanView(SubscribeView):
    template_name = "change_plan.html"


class HistoryView(PaymentsContextMixin, TemplateView):
    template_name = "history.html"


class SubscriptionSuccessView(TemplateView):
    template_name = "subscription_success.html"


class SubscriptionFailureView(TemplateView):
    template_name = "subscription_failure.html"
