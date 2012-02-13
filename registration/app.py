# vim: ai sts=4 sw=4 ts=4 et
import re

from rapidsms.apps.base import AppBase
from rapidsms.models import Contact


class RegistrationApp(AppBase):

    # message pattern expected: 'mileage start number' or 'mileage stop number'
    # in order to take care of possible typos it will accept a mispelled milage
    # for the keyword: 'milage start number' or 'milage stop number'
    pattern = re.compile(r'^(reg|join|register|rej|rejistu)\s+(.+)', re.IGNORECASE)

    def start (self):
        """Configure your app in the start phase."""
        pass

    def parse (self, message):
        """Parse and annotate messages in the parse phase."""
        pass


    def handle(self, message):

        response = self.pattern.findall(message.text)

        if response:

            # FIX ME! Please?!?!
            name = response.pop()[1].encode('ascii', 'replace')

            identity = message.connection.identity

            contact, new = Contact.objects.get_or_create(connection__identity=identity)
            contact.language = 'en'
            contact.phone = identity
            contact.name = name
            contact.save()

            message.connection.contact = contact
            message.connection.save()

            if new:
                message.respond(
                    "Thank you for registering, %(name)s!",
                    name=contact.name)
            else:
                 message.respond(
                    "Thank you %(name)s, your details have been updated.",
                    name=contact.name)
            
        else:
            return False

    def cleanup (self, message):
        """Perform any clean up after all handlers have run in the
           cleanup phase."""
        pass

    def outgoing (self, message):
        """Handle outgoing message notifications."""
        pass

    def stop (self):
        """Perform global app cleanup when the application is stopped."""
        pass