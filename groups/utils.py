""" Utilities for groups """

import re
from django.conf import settings


NUMBER_PATTERN = r'[^0-9]'


def normalize_number(number):
    """ Strip all non-numeric characters from phone numbers """
    normalized_number = re.sub(NUMBER_PATTERN, '', number)
    if len(normalized_number) == 10:
        # missing country code
        if (hasattr(settings, 'COUNTRY_CODE') and settings.COUNTRY_CODE):
            normalized_number = '{0}{1}'.format(settings.COUNTRY_CODE,
                                                normalized_number)
    return normalized_number


COUNTRY_US = '1'
COUNTRY_TH = '66'
COUNTRY_PH = '63'


COUNTRY_MAP = [
    (r'(%s)(\d{3})(\d{3})(\d{4})' % COUNTRY_US, r'+\1 (\2) \3-\4'),
    (r'(%s)(\d{3})(\d{3})(\d{3})' % COUNTRY_TH, r'+\1 \2 \3 \4'),
    (r'(%s)(\d{3})(\d{3})(\d{4})' % COUNTRY_PH, r'+\1 \2 \3 \4'),
]


def format_number(number):
    """
    Take a string of numbers representing a phone number and format it based
    on the country
    """
    for regex, format in COUNTRY_MAP:
        if re.match(regex, number):
            return re.sub(regex, format, number)
    return number
