import re

from django.core.exceptions import ValidationError


phone_re = re.compile(r"\d{1,3}\d{10}$")

def validate_phone(value):
    """ Require country code followed by 10 digits """
    if not phone_re.match(value):
        msg = 'Please enter a number in a format like: XXXYYYZZZZZZZ'
        raise ValidationError(msg)
