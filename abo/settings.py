from django.conf import settings


ABO_BACKENDS = getattr(settings, 'ABO_BACKENDS', tuple())
ABO_DEFAULT_BACKEND = getattr(settings, 'ABO_DEFAULT_BACKEND', '')
ABO_BACKENDS_SETTINGS = getattr(settings, 'ABO_BACKENDS_SETTINGS', dict())

SUBSCRIPTION_MODEL = getattr(settings, 'SUBSCRIPTION_MODEL', 'abo.Subscription')
PLAN_MODEL = getattr(settings, 'PLAN_MODEL', 'abo.Plan')
