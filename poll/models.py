import datetime
import difflib

from django.db import models, transaction, connection
from django.db.models import Sum, Avg, Count, Max, Min, StdDev
from django.contrib.sites.models import Site
from django.contrib.sites.managers import CurrentSiteManager
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django import forms
from django.db.models.query import QuerySet
from django.utils.translation import ugettext as _
from mptt.forms import TreeNodeChoiceField
from rapidsms.models import Contact, Connection

from eav import register
from eav.models import Value, Attribute

from rapidsms.contrib.locations.models import Location
from rapidsms.contrib.locations.nested import models as nested_models
from rapidsms_httprouter.models import Message
from rapidsms_httprouter.managers import BulkInsertManager

from django.conf import settings
import re
from django.utils.translation import (ugettext, activate, deactivate)



# The standard template allows for any amount of whitespace at the beginning,
# followed by the alias(es) for a particular category, followed by any non-
# alphabetical character, or the end of the message
STARTSWITH_PATTERN_TEMPLATE = '^\s*(%s)(\s|[^a-zA-Z]|$)'

CONTAINS_PATTERN_TEMPLATE = '^.*\s*(%s)(\s|[^a-zA-Z]|$)'

# This can be configurable from settings, but here's a default list of
# accepted yes keywords
#YES_WORDS = ['yes', 'yeah', 'yep', 'yay', 'y']

#TODO: Remove tetum from the en
YES_WORDS = {
    'en-us':['yes', 'yeah', 'yep', 'yay', 'y'],
    'en':['yes', 'yeah', 'yep', 'yay', 'y'],
    'ach':['ada','da'],
    'tet':['los','sim',],
}

# This can be configurable from settings, but here's a default list of
# accepted no keywords
NO_WORDS = {
            'en-us':['no', 'nope', 'nah', 'nay', 'n'],
            'en':['no', 'nope', 'nah', 'nay', 'n'],
            'ach':['ku','k'],
            'tet':['lae',],
}

class ResponseForm(forms.Form):
    def __init__(self, data=None, **kwargs):
        response = kwargs.pop('response')
        if data:
            forms.Form.__init__(self, data, **kwargs)
        else:
            forms.Form.__init__(self, **kwargs)
        self.fields['categories'] = forms.ModelMultipleChoiceField(required=False, queryset=response.poll.categories.all(), initial=Category.objects.filter(pk=response.categories.values_list('category', flat=True)))

class NumericResponseForm(ResponseForm):
    value = forms.FloatField()

class LocationResponseForm(ResponseForm):
    value = TreeNodeChoiceField(queryset=Location.tree.all(),
                 level_indicator=u'.', required=True)

class NameResponseForm(ResponseForm):
    value = forms.CharField()

class ResponseCategory(models.Model):
    category = models.ForeignKey('Category')
    response = models.ForeignKey('Response', related_name='categories')
    is_override = models.BooleanField(default=False)
    user = models.ForeignKey(User, null=True)

class Poll(models.Model):
    """
    Polls represent a simple-question, simple-response communication modality
    via SMS.  They can be thought of as a similar to a single datum in an XForm,
    although for now the only data types available are yes/no, free-form text, and
    numeric response.  Fairly simple idea, a poll is created, containing a question
    (the outgoing messages), a list of contacts (those to poll) and an expected
    *type* of response.  The poll can be edited, contact lists modified, etc. via
    the web (the "user"), until it is eventually *started.*  When a poll is started,
    the outgoing question will be sent to all contacts, and any subsequent messages
    coming in from the contacts associated with this poll (until they are polled again)
    will be parsed (or attempted to be parsed) by this poll, and bucketed into a
    particular category.

    FIXME: contact groups, if implemented in core or contrib, should be used here,
           instead of a many-to-many field
    """


    TYPE_TEXT = 't'
    TYPE_NUMERIC = 'n'
    TYPE_LOCATION = 'l'
    TYPE_REGISTRATION = 'r'

    RESPONSE_TYPE_ALL='a'# all all responses
    RESPONSE_TYPE_ONE='o' # allow only one
    RESPONSE_TYPE_NO_DUPS='d'# ignore duplicates

    RESPONSE_TYPE_CHOICES=(
                            (RESPONSE_TYPE_ALL,'Allow all'),
                            (RESPONSE_TYPE_ONE,'Allow one'),
                            (RESPONSE_TYPE_NO_DUPS,'Ignore duplicates')

    )


    TYPE_CHOICES = {
#        TYPE_LOCATION: dict(
#                        label='Location-based',
#                        type=TYPE_LOCATION,
#                        db_type=Attribute.TYPE_OBJECT,
#                        parser=None,
#                        view_template='polls/response_location_view.html',
#                        edit_template='polls/response_location_edit.html',
#                        report_columns=(('Text', 'text'), ('Location', 'location'), ('Categories', 'categories')),
#                        edit_form=LocationResponseForm),
        TYPE_NUMERIC: dict(
                        label='Numeric Response',
                        type=TYPE_NUMERIC,
                        db_type=Attribute.TYPE_FLOAT,
                        parser=None,
                        view_template='polls/response_numeric_view.html',
                        edit_template='polls/response_numeric_edit.html',
                        report_columns=(('Text', 'text'), ('Value', 'value'), ('Categories', 'categories')),
                        edit_form=NumericResponseForm),
        TYPE_TEXT:  dict(
                        label='Free-form',
                        type=TYPE_TEXT,
                        db_type=Attribute.TYPE_TEXT,
                        parser=None,
                        view_template='polls/response_text_view.html',
                        edit_template='polls/response_text_edit.html',
                        report_columns=(('Text', 'text'), ('Categories', 'categories')),
                        edit_form=ResponseForm),
#        TYPE_REGISTRATION:  dict(
#                        label='Name/registration-based',
#                        type=TYPE_REGISTRATION,
#                        db_type=Attribute.TYPE_TEXT,
#                        parser=None,
#                        view_template='polls/response_registration_view.html',
#                        edit_template='polls/response_registration_edit.html',
#                        report_columns=(('Text', 'text'), ('Categories', 'categories')),
#                        edit_form=NameResponseForm),
    }

    name = models.CharField(max_length=32,
                            help_text="Human readable name.")
    question = models.CharField(_("question"),max_length=160)
    messages = models.ManyToManyField(Message, null=True)
    contacts = models.ManyToManyField(Contact, related_name='polls')
    user = models.ForeignKey(User)
    start_date = models.DateTimeField(null=True)
    end_date = models.DateTimeField(null=True)
    type = models.SlugField(max_length=8, null=True, blank=True)
    default_response = models.CharField(_("default_response"),max_length=160)
    sites = models.ManyToManyField(Site)
    objects = models.Manager()
    on_site = CurrentSiteManager('sites')
    bulk = BulkInsertManager()
    response_type=models.CharField(max_length=1,choices=RESPONSE_TYPE_CHOICES,default=RESPONSE_TYPE_ALL,null=True,blank=True)

    class Meta:
        permissions = (
            ("can_poll", "Can send polls"),
            ("can_edit_poll", "Can edit poll rules, categories, and responses"),
        )
        ordering=["-end_date"]

    @classmethod
    def register_poll_type(cls, field_type, label, parserFunc, \
                           db_type=TYPE_TEXT, \
                           view_template=None, \
                           edit_template=None, \
                           report_columns=None, \
                           edit_form=None):
        """
        Used to register a new question type for Polls.  You can use this method to build new question types that are
        available when building Polls.  These types may just do custom parsing of the SMS text sent in, then stuff
        those results in a normal core datatype, or they may lookup and reference completely custom attributes.

        Arguments are:
           label:       The label used for this field type in the user interface
           field_type:  A slug to identify this field type, must be unique across all field types
           parser:      The function called to turn the raw string into the appropriate type, should take one argument:
                        'value' the string value submitted.
           db_type:     How the value will be stored in the database, can be one of: TYPE_FLOAT, TYPE_TEXT or TYPE_OBJECT
                        (defaults to TYPE_TEXT)
           [view_template]: A template that renders an individual row in a table displaying responses
           [edit_template]: A template that renders an individual row for editing a response
           [report_columns]: the column labels for a table of responses for a poll of a particular type
           [edit_form]: A custom edit form for editing responses
        """
        # set the defaults
        if view_template is None:
            view_template = 'polls/response_custom_view.html'
        if edit_template is None:
            edit_template = 'polls/response_custom_edit.html'
        if report_columns is None:
            report_columns = (('Original Text', 'text'), ('Value', 'custom'))

        Poll.TYPE_CHOICES[field_type] = dict(
            type=field_type, label=label,
            db_type=db_type, parser=parserFunc,
            view_template=view_template,
            edit_template=edit_template,
            report_columns=report_columns,
            edit_form=edit_form)

    @classmethod
    @transaction.commit_on_success
    def create_with_bulk(cls, name, type, question, default_response, contacts, user):
        #import pdb; pdb.set_trace()
        localized_messages={}
        for language in dict(settings.LANGUAGES).keys():
            if language == "en":
                """default to English for contacts with no language preference"""
                localized_contacts=contacts.filter(language__in=["en",''])
            else:

                localized_contacts=contacts.filter(language=language)
            #if localized_contacts.exists():
            #    messages = Message.mass_text(gettext_db(field=question,language=language), Connection.objects.filter(contact__in=list(localized_contacts)).distinct(), status='L')
            #    localized_messages[language] = [messages,localized_contacts]
        poll = Poll.objects.create(name=name, type=type, question=question, default_response=default_response, user=user)

        # This is the fastest (pretty much only) was to get contacts and messages M2M into the
        # DB fast enough at scale
        cursor = connection.cursor()
        for language in localized_messages.keys():
            for c in localized_messages.get(language)[1]:
                raw_sql = "insert into poll_poll_contacts (poll_id, contact_id) values (%d, %d)" % (poll.pk, c.pk)
                #print raw_sql
                cursor.execute(raw_sql)

            for m in localized_messages.get(language)[0]:
                raw_sql = "insert into poll_poll_messages (poll_id, message_id) values (%d,%d)" % (poll.pk, m.pk)
                #print raw_sql
                cursor.execute(raw_sql)

        transaction.commit_unless_managed()
        if 'django.contrib.sites' in settings.INSTALLED_APPS:
            poll.sites.add(Site.objects.get_current())
        return poll

    def add_yesno_categories(self):
        """
        This creates a generic yes/no poll categories for a particular poll
        """
        langs = self.contacts.values_list('language',flat=True).distinct()
        #langs = dict(settings.LANGUAGES).keys()
        self.categories.create(name='yes', color='99ff77')
        self.categories.create(name='no', color='ff9977')
        self.categories.create(name='unknown', color='ffff77',default=True, error_category=True)

        # add one rule to yes category per language
        for l in langs:
            no_rule_string = '|'.join(NO_WORDS[l])
            yes_rule_string = '|'.join(YES_WORDS[l])

            self.categories.get(name='yes').rules.create(
                regex=(STARTSWITH_PATTERN_TEMPLATE % yes_rule_string ),
                rule_type=Rule.TYPE_REGEX,
                rule_string=(STARTSWITH_PATTERN_TEMPLATE % yes_rule_string))

            self.categories.get(name='no').rules.create(
                regex=(STARTSWITH_PATTERN_TEMPLATE % no_rule_string),
                rule_type=Rule.TYPE_REGEX,
                rule_string=(STARTSWITH_PATTERN_TEMPLATE % no_rule_string))


    def is_yesno_poll(self):
        return self.categories.count() == 3 and \
            self.categories.filter(name='yes').count() and \
            self.categories.filter(name='no').count() and \
            self.categories.filter(name='unknown').count()

    @transaction.commit_on_success
    def start(self):
        """
        This starts the poll: outgoing messages are sent to all the contacts
        registered with this poll, and the start date is updated accordingly.
        All incoming messages from these users will be considered as
        potentially a response to this poll.
        """
        self.messages.update(status='P')
        self.start_date = datetime.datetime.now()
        self.save()


    def end(self):
        self.end_date = datetime.datetime.now()
        self.save()

    def reprocess_responses(self):
        for rc in ResponseCategory.objects.filter(category__poll=self, is_override=False):
            rc.delete()

        for resp in self.responses.all():
            resp.has_errors = False
            for category in self.categories.all():
                for rule in category.rules.all():
                    regex = re.compile(rule.regex)
                    if resp.eav.poll_text_value:
                        if regex.search(resp.eav.poll_text_value.lower()) and not resp.categories.filter(category=category).count():
                            if category.error_category:
                                resp.has_errors = True
                            rc = ResponseCategory.objects.create(response=resp, category=category)
                            break
            if not resp.categories.all().count() and self.categories.filter(default=True).count():
                if self.categories.get(default=True).error_category:
                    resp.has_errors = True
                resp.categories.add(ResponseCategory.objects.create(response=resp, category=self.categories.get(default=True)))
            resp.save()

    def process_response(self, message):
        db_message = None
        if hasattr(message, 'db_message'):
            db_message = message.db_message
        resp = Response.objects.create(poll=self, message=db_message, contact=db_message.connection.contact, date=db_message.date)
        outgoing_message = self.default_response
        if (self.type == Poll.TYPE_LOCATION):
            location_template = STARTSWITH_PATTERN_TEMPLATE % '[a-zA-Z]*'
            regex = re.compile(location_template)
            if regex.search(message.text):
                spn = regex.search(message.text).span()
                location_str = message.text[spn[0]:spn[1]]
                area = None
                area_names = Location.objects.all().values_list('name', flat=True)
                area_names_lower = [ai.lower() for ai in area_names]
                area_names_matches = difflib.get_close_matches(location_str.lower(), area_names_lower)
                if area_names_matches:
                    area = Location.objects.filter(name__iexact=area_names_matches[0])[0]
                    resp.eav.poll_location_value = area
                    resp.save()
                else:
                    resp.has_errors = True

            else:
                resp.has_errors = True

        elif (self.type == Poll.TYPE_NUMERIC):
            try:
                regex = re.compile(r"(-?\d+(\.\d+)?)")
                #split the text on number regex. if the msg is of form
                #'19'or '19 years' or '19years' or 'age19'or 'ugx34.56shs' it returns a list of length 4
                msg_parts = regex.split(message.text)
                if len(msg_parts) == 4 :
                    resp.eav.poll_number_value = float(msg_parts[1])
                else:
                     resp.has_errors = True
            except IndexError:
                resp.has_errors = True

        elif ((self.type == Poll.TYPE_TEXT) or (self.type == Poll.TYPE_REGISTRATION)):
            resp.eav.poll_text_value = message.text
            if self.categories:
                for category in self.categories.all():
                    for rule in category.rules.all():
                        regex = re.compile(rule.regex)
                        if regex.search(message.text.lower()):
                            rc = ResponseCategory.objects.create(response=resp, category=category)
                            resp.categories.add(rc)
                            if category.error_category:
                                resp.has_errors = True
                                outgoing_message = category.response
                            break

        elif self.type in Poll.TYPE_CHOICES:
            typedef = Poll.TYPE_CHOICES[self.type]
            try:
                cleaned_value = typedef['parser'](message.text)
                if typedef['db_type'] == Attribute.TYPE_TEXT:
                    resp.eav.poll_text_value = cleaned_value
                elif typedef['db_type'] == Attribute.TYPE_FLOAT or \
                     typedef['db_type'] == Attribute.TYPE_INT:
                    resp.eav.poll_number_value = cleaned_value
                elif typedef['db_type'] == Attribute.TYPE_OBJECT:
                    resp.eav.poll_location_value = cleaned_value
            except ValidationError as e:
                resp.has_errors = True
                if getattr(e, 'messages', None):
                    outgoing_message = str(e.messages[0])
                else:
                    outgoing_message = None

        if not resp.categories.all().count() and self.categories.filter(default=True).count():
            resp.categories.add(ResponseCategory.objects.create(response=resp, category=self.categories.get(default=True)))
            if self.categories.get(default=True).error_category:
                resp.has_errors = True
                outgoing_message = self.categories.get(default=True).response

        if (not resp.has_errors or not outgoing_message):
            for respcategory in resp.categories.order_by('category__priority'):
                if respcategory.category.response:
                    outgoing_message = respcategory.category.response
                    break
        resp.save()
        if not outgoing_message:
            return (resp, None,)
        else:
            if db_message.connection.contact and  db_message.connection.contact.language:
                outgoing_message=gettext_db(language=db_message.connection.contact.language,field=outgoing_message)

            return (resp, outgoing_message,)

    def get_numeric_detailed_data(self):
        return Value.objects.filter(attribute__slug='poll_number_value', entity_ct=ContentType.objects.get_for_model(Response), entity_id__in=self.responses.all()).values_list('value_float').annotate(Count('value_float')).order_by('-value_float')

    def get_numeric_report_data(self, location=None, for_map=None):
        if location:
            q = Value.objects.filter(attribute__slug='poll_number_value', entity_ct=ContentType.objects.get_for_model(Response), entity_id__in=self.responses.all())
            q = q.extra(tables=['poll_response', 'rapidsms_contact', 'locations_location', 'locations_location'],
                    where=['poll_response.id = eav_value.entity_id',
                           'rapidsms_contact.id = poll_response.contact_id',
                           'locations_location.id = rapidsms_contact.reporting_location_id',
                           'T7.id in %s' % (str(tuple(location.get_children().values_list('pk', flat=True)))),
                           'T7.lft <= locations_location.lft', \
                           'T7.rght >= locations_location.rght', \
                           ],
                    select={
                        'location_name':'T7.name',
                        'location_id':'T7.id',
                        'lft':'T7.lft',
                        'rght':'T7.rght',
                    }).values('location_name', 'location_id')

        else:
            q = Value.objects.filter(attribute__slug='poll_number_value', entity_ct=ContentType.objects.get_for_model(Response), entity_id__in=self.responses.all()).values('entity_ct')
        q = q.annotate(Sum('value_float'), Count('value_float'), Avg('value_float'), StdDev('value_float'), Max('value_float'), Min('value_float'))
        return q

    def responses_by_category(self, location=None, for_map=True):
        categorized = ResponseCategory.objects.filter(response__poll=self)
        uncategorized = self.responses.exclude(pk__in=ResponseCategory.objects.filter(response__poll=self).values_list('response', flat=True))
        uvalues = ['poll__pk']

        if location:
            if location.get_children().count() == 1:
                location_where = 'T9.id = %d' % location.get_children()[0].pk
                ulocation_where = 'T7.id = %d' % location.get_children()[0].pk
            elif location.get_children().count() == 0:
                location_where = 'T9.id = %d' % location.pk
                ulocation_where = 'T7.id = %d' % location.pk
            else:
                location_where = 'T9.id in %s' % (str(tuple(location.get_children().values_list('pk', flat=True))))
                ulocation_where = 'T7.id in %s' % (str(tuple(location.get_children().values_list('pk', flat=True))))

            where_list = [\
                          'T9.lft <= locations_location.lft', \
                          'T9.rght >= locations_location.rght', \
                          location_where, \
                          'T9.point_id = locations_point.id', ]
            select = {
                        'location_name':'T9.name',
                        'location_id':'T9.id',
                        'lat':'locations_point.latitude',
                        'lon':'locations_point.longitude',
                        'rght':'T9.rght',
                        'lft':'T9.lft',
                    }
            tables = ['locations_location', 'locations_point']
            if not for_map:
                where_list = where_list[:3]
                select.pop('lat')
                select.pop('lon')
                tables = tables[:1]
            categorized = categorized\
                    .values('response__message__connection__contact__reporting_location__name')\
                    .extra(tables=tables, \
                           where=where_list)\
                    .extra(select=select)

            uwhere_list = [\
                          'T7.lft <= locations_location.lft', \
                          'T7.rght >= locations_location.rght', \
                          ulocation_where, \
                          'T7.point_id = locations_point.id', ]
            uselect = {
                        'location_name':'T7.name',
                        'location_id':'T7.id',
                        'lat':'locations_point.latitude',
                        'lon':'locations_point.longitude',
                        'rght':'T7.rght',
                        'lft':'T7.lft',
                    }
            uvalues = ['location_name', 'location_id', 'lat', 'lon']
            utables = ['locations_location', 'locations_point']
            if not for_map:
                uwhere_list = uwhere_list[:3]
                uselect.pop('lat')
                uselect.pop('lon')
                uvalues = uvalues[:2]
                utables = utables[:1]

            uncategorized = uncategorized\
                    .values('message__connection__contact__reporting_location__name')\
                    .extra(tables=utables, \
                           where=uwhere_list)\
                    .extra(select=uselect)

            values_list = ['location_name', 'location_id', 'category__name', 'category__color', 'lat', 'lon', ]
            if not for_map:
                values_list = values_list[:4]
        else:
            values_list = ['category__name', 'category__color']

        categorized = categorized.values(*values_list)\
                      .annotate(value=Count('pk'))\
                      .order_by('category__name')

        uncategorized = uncategorized.values(*uvalues).annotate(value=Count('pk'))

        if location:
            categorized = categorized.extra(order_by=['location_name'])
            uncategorized = uncategorized.extra(order_by=['location_name'])
            if for_map:
                for d in uncategorized:
                    d['lat'] = '%.5f' % float(d['lat'])
                    d['lon'] = '%.5f' % float(d['lon'])
                for d in categorized:
                    d['lat'] = '%.5f' % float(d['lat'])
                    d['lon'] = '%.5f' % float(d['lon'])

        if len(uncategorized):
            uncategorized = list(uncategorized)
            for d in uncategorized:
                d.update({'category__name':'uncategorized', 'category__color':''})
            categorized = list(categorized) + uncategorized

        return categorized

    def __unicode__(self):
        return self.question

class Category(models.Model):
    """
    A category is a 'bucket' that an incoming poll response is placed into.

    Categories have rules, which are regular expressions that a message must
    satisfy to belong to a particular category (otherwise a response will have
    None for its category). FIXME does this make sense, or should all polls
    have a default 'unknown' category?
    """
    name = models.CharField(max_length=50)
    poll = models.ForeignKey(Poll, related_name='categories')
    priority = models.PositiveSmallIntegerField(null=True)
    color = models.CharField(max_length=6)
    default = models.BooleanField(default=False)
    response = models.CharField(max_length=160, null=True)
    error_category = models.BooleanField(default=False)

    class Meta:
        ordering = ['name']

    @classmethod
    def clear_defaults(cls, poll):
        for c in Category.objects.filter(poll=poll, default=True):
            c.default = False
            c.save()

    def __unicode__(self):
        return u'%s' % self.name

class Response(models.Model):
    """
    Responses tie incoming messages from poll participants to a particular
    bucket that their response is associated with.  Web users may also be
    able to override a particular response as belonging to a particular
    category, which shouldn't be overridden by new rules.
    """
    message = models.ForeignKey(Message, null=True, related_name='poll_responses')
    poll = models.ForeignKey(Poll, related_name='responses')
    contact = models.ForeignKey(Contact, null=True, blank=True, related_name='responses')
    date = models.DateTimeField(auto_now_add=True)
    has_errors = models.BooleanField(default=False)

    def update_categories(self, categories, user):
        for c in categories:
            if not self.categories.filter(category=c).count():
                ResponseCategory.objects.create(response=self, category=c, is_override=True, user=user)
        for rc in self.categories.all():
            if not rc.category in categories:
                rc.delete()

register(Response)

class Rule(models.Model):
    """
    A rule is a regular expression that an incoming message text might
    satisfy to belong in a particular category.  A message must satisfy
    one or more rules to belong to a category.
    """

    TYPE_STARTSWITH = 'sw'
    TYPE_CONTAINS = 'c'
    TYPE_REGEX = 'r'
    RULE_CHOICES = (
         (TYPE_STARTSWITH, 'Starts With'),
         (TYPE_CONTAINS, 'Contains'),
         (TYPE_REGEX, 'Regex (advanced)'))

    RULE_DICTIONARY = {
         TYPE_STARTSWITH: 'Starts With',
         TYPE_CONTAINS: 'Contains',
         TYPE_REGEX: 'Regex (advanced)',
    }

    regex = models.CharField(max_length=256)
    category = models.ForeignKey(Category, related_name='rules')
    rule_type = models.CharField(max_length=2, choices=RULE_CHOICES)
    rule_string = models.CharField(max_length=256, null=True)

    @property
    def rule_type_friendly(self):
        return Rule.RULE_DICTIONARY[self.rule_type]

    def update_regex(self):
        if self.rule_type == Rule.TYPE_STARTSWITH:
            self.regex = STARTSWITH_PATTERN_TEMPLATE % self.rule_string
        elif self.rule_type == Rule.TYPE_CONTAINS:
            self.regex = CONTAINS_PATTERN_TEMPLATE % self.rule_string
        elif self.rule_type == Rule.TYPE_REGEX:
            self.regex = self.rule_string


class Translation(models.Model):
    field = models.TextField( db_index=True)
    language = models.CharField(max_length=5, db_index=True,
                                choices=settings.LANGUAGES)
    value = models.TextField(blank=True)
    def __unicode__(self):
        return u'%s: %s' % (self.language, self.value)

    class Meta:
        unique_together = ('field', 'language')


def gettext_db(field,language):
    #if name exists in po file get it else look
    if Translation.objects.filter(field=field,language=language).exists():
       return Translation.objects.filter(field=field,language=language)[0].value
    else:
       activate(language)
       lang_str=ugettext(field)
       deactivate()
       return lang_str
