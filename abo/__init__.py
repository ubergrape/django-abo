from . import settings
from django.core.exceptions import ImproperlyConfigured


def get_plan_model():
    """
    Returns the Plan model that is active in this project.
    """
    from django.db.models import get_model

    try:
        app_label, model_name = settings.PLAN_MODEL.split('.')
    except ValueError:
        raise ImproperlyConfigured("PLAN_MODEL must be of the form 'app_label.model_name'")
    plan_model = get_model(app_label, model_name)
    if plan_model is None:
        raise ImproperlyConfigured("PLAN_MODEL refers to model '%s' that has not been installed" % settings.PLAN_MODEL)
    return plan_model


def get_subscription_model():
    """
    Returns the Subscription model that is active in this project.
    """
    from django.db.models import get_model

    try:
        app_label, model_name = settings.SUBSCRIPTION_MODEL.split('.')
    except ValueError:
        raise ImproperlyConfigured("SUBSCRIPTION_MODEL must be of the form 'app_label.model_name'")
    subscription_model = get_model(app_label, model_name)
    if subscription_model is None:
        raise ImproperlyConfigured("SUBSCRIPTION_MODEL refers to model '%s' that has not been installed" % settings.SUBSCRIPTION_MODEL)
    return subscription_model
