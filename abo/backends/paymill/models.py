from django.db import models
from django.utils.translation import ugettext_lazy as _

from abo.fields import JSONField


class Event(models.Model):
    received_at = models.DateTimeField(_("received at"), auto_now_add=True, db_index=True)
    event_type = models.CharField(max_length=250)
    data = JSONField()
