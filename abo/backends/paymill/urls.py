from django.conf.urls import patterns, url
from .views import PaymillView, webhook


urlpatterns = patterns('',
    url(r'subscribe/$', PaymillView.as_view(), name='abo-paymill-authorization'),
    url(r'^webhook/(?P<secret>\w{32})$', webhook, name='abo-paymill-webhook')
)
