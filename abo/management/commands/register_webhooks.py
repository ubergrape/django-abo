from django.core.management import BaseCommand

from abo.utils import import_backend_modules, import_name


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        backends = import_backend_modules()

        for name, cls_name in backends.iteritems():
            try:
                webhook_module = import_name(name + ".webhooks")

            except AttributeError:
                # this module has no webhooks, just ignore it.
                print "Backend '%s' has no webhooks" % name
                continue

            print "Registering webhook for backend '%s'" % name
            webhook = webhook_module.Webhook()
            webhook.init_webhook()
            print "Webhook URL: %s" % webhook.get_url()
