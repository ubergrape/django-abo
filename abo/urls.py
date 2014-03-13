from django.conf.urls import patterns, url, include

from abo.utils import import_backend_modules


backend_specific_urls = []
for backend_name, urls in import_backend_modules('urls').items():
    simple_name = backend_name.split('.')[-1]
    backend_specific_urls.append(url(r'^%s/' % simple_name, include(urls)))


from .views import (
    CancelView,
    ChangeCardView,
    ChangePlanView,
    HistoryView,
    SubscribeView,
    SubscriptionSuccessView,
    SubscriptionFailureView
)

urlpatterns = patterns('',
    url(r"^subscribe/$", SubscribeView.as_view(), name="abo-subscribe"),
    url(r"^subscription/(?P<pk>\d+)/success/$", SubscriptionSuccessView.as_view(), name="abo-success"),
    url(r"^subscription/(?P<pk>\d+)/failure/$", SubscriptionFailureView.as_view(), name="abo-failure"),
    url(r"^change/card/$", ChangeCardView.as_view(), name="abo-change_card"),
    url(r"^change/plan/$", ChangePlanView.as_view(), name="abo-change_plan"),
    url(r"^cancel/$", CancelView.as_view(), name="abo-cancel"),
    url(r"^history/$", HistoryView.as_view(), name="abo-history"),
    *backend_specific_urls
)
