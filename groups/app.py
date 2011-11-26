from rapidsms.apps.base import AppBase
from rapidsms.models import Contact

from groups.utils import normalize_number


class GroupsApp(AppBase):

    number_pattern = r'[^0-9]'

    def _normalize_number(self, number):
        return normalize_number(number)

    def _associate_contact(self, connection):
        normalized_number = normalize_number(connection.identity)
        self.debug('Normalized number: {0}'.format(normalized_number))
        try:
            contact = Contact.objects.get(phone=normalized_number)
        except Contact.DoesNotExist:
            self.debug('Failed to find matching contact')
            contact = None
        if contact:
            self.debug('Associating connection to {0}'.format(contact))
            connection.contact = contact
            connection.save()

    def filter(self, msg):
        if not msg.connection.contact:
            self.debug('Found {0} without contact'.format(msg.connection))
            self._associate_contact(msg.connection)
