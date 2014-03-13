django-abo
==========

Recurring Payment / Subscription Handling for Django, supporting different payment gateways


**Currently django-abo is in alpha/beta phase, please use with caution!**

## Contribute

If you have a good idea or a specific problem, let us know! We'd love to get some feedback and we need more backends.

If you see a bug or want to contribute code in any way, please create a pull request on GitHub.

If you want to discuss changes (without comitting code), please create an issue on GitHub.

## Supported Backends

* [Paymill](https://www.paymill.com/)


## Installation

```bash
pip install django-abo
```

## Definitions

* *Plan* = something a customer can subscribe to, for example: "Premium Plan, 10$/month"
* *Subscription* = an actual subscription from a customer to a plan

## Usage

### 1. Setup settings

Add `abo` to your `INSTALLED_APPS`:
```python
INSTALLED_APPS = (
    # ...
    'abo',
)
```

Add these lines to your settings:

```python
ABO_BACKENDS = ('abo.backends.paymill', )
INSTALLED_APPS += ABO_BACKENDS

ABO_DEFAULT_BACKEND = 'abo.backends.paymill'

ABO_BACKENDS_SETTINGS = {
    'abo.backends.paymill': {
        'PAYMILL_PUBLIC_KEY': 'your public key',
        'PAYMILL_PRIVATE_KEY': 'your private key',
        'PAYMILL_WEBHOOK_HOST': ''  # hint: use ngrok.com for testing
    }
}
```

### 2. Setup URLs

Include the payment URLs in your `urls.py`:

```python
urlpatterns = patterns('',
    # ...
    url(r'payment/^', include('abo.urls')),
)
```

Now, open http://localhost:8000/payment/subscribe/

### 3. Optional: Custom templates

*django-abo* comes with it's own templates so you don't have to start from scratch.

You can override backend specific templates and generic templates.

1. Just create a `abo` subdirectory in your own templates directory and put your own templates there.
1. Make sure they have the same filename as the original ones.

For example, start with [subscription_success.html](https://github.com/ubergrape/django-abo/blob/master/abo/templates/subscription_success.html)

### 4. Optional: Create your own plan and subscription models

*django-abo* has two models you can easily extend. If you have ever swapped Django's default user model for your own, you'll see that the technique is very similar.

#### Example custom Subscription model

Let's say you have an `Organization` model in your `accounts` app and you want every `Subscription` object to belong to an organization.

1. Create an app, if you don't have one already, that should contain your own `Subscription` model. For example `payment`

1. Put your custom `Subscription` model in your `models.py`, subclassing `AbstractSubscription`.

    ```python
    from django.db import models

    from accounts.models import Organization
    from abo.models import AbstractSubscription

    class Organization(models.Model):
        name

    class Subscription(AbstractSubscription):
        organization = models.ForeignKey(Organization, null=True)
    ```

1. Put this in your settings:

   ```python
   SUBSCRIPTION_MODEL = 'payment.Subscription'
   ```

1. Create your own View for Paymill:

    ```python
    from abo.backends.paymill.views import PaymillView

    class CustomPaymillView(PaymillView):
        def form_valid(self, form):
            r = super(CustomPaymillView, self).form_valid(form)

            # Let's assume you have a middleware that puts the organization in request.
            self.subscription.organization = self.request.organization
            self.subscription.save()

            return r
    ```

1. Put it in your urls.py

    ```python
    urlpatterns = patterns('',
        # ...
        url(r'^paymill/subscribe/$', CustomPaymillView.as_view(), name='abo-paymill-authorization'),
        url(r'^', include('abo.urls')),
    )

#### Custom Plan model

The same works for the `Plan` model. If you created your custom `Plan` model, let *django-abo* know where it is:

```python
PLAN_MODEL = 'payment.Plan'
```

