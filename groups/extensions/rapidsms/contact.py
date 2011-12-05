from django.db import models
from django.utils.translation import ugettext as _
from django.contrib.auth.models import User

from rapidsms.models import Backend

from groups.utils import format_number


class ContactExtra(models.Model):
    """ Abstract model to extend the RapidSMS Contact model """

    phone = models.CharField(max_length=32,)
    #gender = models.CharField(
    #        max_length=1,
    #        choices=(('M', 'Male'), ('F', 'Female')), null=True)
    age = models.IntegerField(blank=True, null=True)
    location = models.CharField(max_length=64, blank=True, null=True)
    
    def save(self, **kwargs):
        super(ContactExtra, self).save(**kwargs)

    class Meta:
        abstract = True

    @property
    def formatted_phone(self):
        return format_number(self.phone)
