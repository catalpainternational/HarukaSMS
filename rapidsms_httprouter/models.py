import datetime
from django.db import models

from rapidsms.models import Contact, Connection

from .managers import ForUpdateManager, BulkInsertManager

DIRECTION_CHOICES = (
    ("I", "Incoming"),
    ("O", "Outgoing"))

STATUS_CHOICES = (
    ("R", "Received"),
    ("H", "Handled"),

    ("P", "Processing"),
    ("L", "Locked"),

    ("Q", "Queued"),
    ("S", "Sent"),
    ("D", "Delivered"),

    ("C", "Cancelled"),
    ("E", "Errored")
)

#
# Allows us to use SQL to lock a row when setting it to 'locked'.  Without this
# in a multi-process environment like Gunicorn we'll double send messages.
#
# See: https://coderanger.net/2011/01/select-for-update/
#

class Message(models.Model):
    connection = models.ForeignKey(Connection, related_name='messages')
    text       = models.TextField()
    direction  = models.CharField(max_length=1, choices=DIRECTION_CHOICES)
    status     = models.CharField(max_length=1, choices=STATUS_CHOICES)
    date       = models.DateTimeField(auto_now_add=True)

    in_response_to = models.ForeignKey('self', related_name='responses', null=True)
    application = models.CharField(max_length=100, null=True)

    # set our manager to our update manager
    objects = ForUpdateManager()
    bulk = BulkInsertManager()

    def __unicode__(self):
        # crop the text (to avoid exploding the admin)
        if len(self.text) < 60: str = self.text
        else: str = "%s..." % (self.text[0:57])

        to_from = (self.direction == "I") and "to" or "from"
        return "%s (%s %s)" % (str, to_from, self.connection.identity)

    def as_json(self):
        return dict(id=self.pk,
                    contact=self.connection.identity, backend=self.connection.backend.name,
                    direction=self.direction, status=self.status, text=self.text,
                    date=self.date.isoformat())

    @classmethod
    def mass_text(cls, text, connections, status='P'):
        for connection in connections:
            Message.bulk.bulk_insert(
                send_pre_save=False,
                text=text,
                direction='O',
                status=status,
                connection=connection)
        return Message.bulk.bulk_insert_commit(send_post_save=False, autoclobber=True)
