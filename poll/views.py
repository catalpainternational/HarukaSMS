# -*- coding: utf-8 -*-
import csv
from django import forms
from django.db import transaction
from django.db.models import Q, Count
from django.views.decorators.http import require_GET
from django.template import RequestContext
from django.shortcuts import redirect, get_object_or_404, render_to_response
from django.http import HttpResponse
from django.contrib.sites.models import Site
from django.contrib.auth.decorators import login_required, permission_required
from django.utils import simplejson
from django.utils.safestring import mark_safe
from rapidsms_httprouter.router import get_router
from rapidsms.messages.outgoing import OutgoingMessage
from .models import Response
from rapidsms.contrib.locations.models import Location
from rapidsms.models import Contact, Connection, Backend
from eav.models import Attribute
from django.core.urlresolvers import reverse
from django.views.decorators.cache import cache_control
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage
from rapidsms_httprouter.models import Message
from rapidsms_httprouter.views import MessageTable

from .forms import *



def _mail_merge(contact, text):
    # use regex!!!
    text = text.replace('[name]', contact.name)
    text = text.replace('[ name]', contact.name)
    text = text.replace('[name ]', contact.name)
    text = text.replace('[ name ]', contact.name)

    text = text.replace('[first_name]', contact.name.split()[0])
    text = text.replace('[ first_name]', contact.name.split()[0])
    text = text.replace('[first_name ]', contact.name.split()[0])
    text = text.replace('[ first_name ]', contact.name.split()[0])
    return text

@require_GET
@login_required
def responses_as_csv(req, pk):
    """ CSV export """
    poll = get_object_or_404(Poll, pk=pk)

    responses = poll.responses.all().order_by('-pk')
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=export.csv'

    writer = csv.writer(response)
    writer.writerow(['Date', 'Phone Number', 'Poll', 'Response'])
    for r in responses:
        writer.writerow([r.date, r.message.connection.identity, r.poll, r.message.text])
    return response


class ReplyForm(forms.Form):
    recipient = forms.CharField(max_length=20)
    message = forms.CharField(max_length=160, widget=forms.TextInput(attrs={'size':'60'}))



@login_required
def dashboard(req):
    """ dashboard for viewing poll status and incoming / outgoing messages """
    polls = Poll.objects.annotate(Count('responses')).order_by('start_date')[:5]
    messages = Message.objects.all().order_by('-date')[0:15]

    # get some real names per connection
    for message in messages:
        message.connection.name = Contact.objects.get(connection__identity=message.connection.identity).name

    # prepare for the message table
    titles=["Text","Direction","Phone number","Status","Date"]
    table = read_only_message_table(messages,titles)

    if req.method.upper() == 'GET':
        reply_form = ReplyForm()

    elif req.POST['action'].upper() == 'REPLY':
            reply_form = ReplyForm(req.POST)
            if reply_form.is_valid():
                if Connection.objects.filter(identity=reply_form.cleaned_data['recipient']).count():
                    text = reply_form.cleaned_data['message']
                    conn = Connection.objects.filter(identity=reply_form.cleaned_data['recipient'])[0]
                    text = _mail_merge(Contact.objects.get(connection__identity=conn.identity), text)
                    outgoing = OutgoingMessage(conn, text)
                    get_router().handle_outgoing(outgoing)
            else:
                reply_form.errors.setdefault('short_description', ErrorList())
                reply_form.errors['recipient'].append("This number isn't in the system")

    return render_to_response(
        "polls/poll_dashboard.html",
        { "polls": polls,
          "reply_form" : reply_form,
          "messages_table": table},
        context_instance=RequestContext(req))

@require_GET
@login_required
def latest_messages(req):
    """ return -json- HTML with latest messages """
    queryset = Message.objects.all()
    titles=["Text","Direction","Phone number","Status","Date"]
    table = read_only_message_table(queryset.order_by('-date')[0:15],titles)

    return HttpResponse(status=200,content=table)

@require_GET
@login_required
def polls(req):
    polls = Poll.objects.annotate(Count('responses')).order_by('start_date')
    breadcrumbs = (('Polls', ''),)
    return render_to_response(
        "polls/poll_index.html",
        { 'polls': polls, 'breadcrumbs': breadcrumbs },
        context_instance=RequestContext(req))


def demo(req, poll_id):
    poll = get_object_or_404(Poll, pk=poll_id)
    b1, created = Backend.objects.get_or_create(name="dmark")
    # Terra
    c1, created = Connection.objects.get_or_create(identity="256785137868", defaults={
        'backend':b1,
    })
    # Sharad
    b2, created = Backend.objects.get_or_create(name="utl")
    c2, created = Connection.objects.get_or_create(identity="256717171100", defaults={
        'backend':b2,
    })
    router = get_router()
    outgoing = OutgoingMessage(c1, "dear Bulambuli representative: uReport, Uganda's community-level monitoring system, shows that 75% of young reporters in your district found that their local water point IS NOT functioning.")
    router.handle_outgoing(outgoing)
    outgoing = OutgoingMessage(c2, "dear Amuru representative: uReport, Uganda's community-level monitoring system, shows that 46.7% of young reporters in your district found that their local water point IS NOT functioning.")
    router.handle_outgoing(outgoing)
    return HttpResponse(status=200)

@permission_required('poll.can_poll')
def new_poll(req):
    if req.method == 'POST':
        form = NewPollForm(req.POST)
        form.updateTypes()
        if form.is_valid():
            # create our XForm
            question = form.cleaned_data['question']
            default_response = form.cleaned_data['default_response']
            contacts = form.cleaned_data['contacts']
            if hasattr(Contact, 'groups'):
                groups = form.cleaned_data['groups']
                contacts = Contact.objects.filter(Q(pk__in=contacts) | Q(groups__in=groups)).distinct()
            name = form.cleaned_data['name']
            p_type = form.cleaned_data['poll_type']
            response_type = form.cleaned_data['response_type']
            if not form.cleaned_data['default_response_luo'] == '' and not form.cleaned_data['default_response'] == '':
                Translation.objects.create(language='ach', field=form.cleaned_data['default_response'],
                                           value=form.cleaned_data['default_response_luo'])

            if not form.cleaned_data['question_luo'] == '':
                Translation.objects.create(language='ach', field=form.cleaned_data['question'],
                                           value=form.cleaned_data['question_luo'])

            poll_type = Poll.TYPE_TEXT if p_type == NewPollForm.TYPE_YES_NO else p_type

            poll = Poll.create_with_bulk(\
                                 name,
                                 poll_type,
                                 question,
                                 default_response,
                                 contacts,
                                 req.user)
            poll.contacts=contacts # for some reason this wasn't being saved in the create_with_bulk call
            poll.response_type=response_type
            poll.save()

            if p_type == NewPollForm.TYPE_YES_NO:
                poll.add_yesno_categories()

            if settings.SITE_ID:
                poll.sites.add(Site.objects.get_current())
            if form.cleaned_data['start_immediately']:
                poll.start()

            return redirect(reverse('poll.views.view_poll', args=[poll.pk]))
    else:
        form = NewPollForm()
        form.updateTypes()

    return render_to_response(
        "polls/poll_create.html", { 'form': form},
        context_instance=RequestContext(req))

@login_required
def view_poll(req, poll_id):
    poll = get_object_or_404(Poll, pk=poll_id)
    categories = Category.objects.filter(poll=poll)
    breadcrumbs = (('Polls', reverse('polls')), ('Edit Poll', ''))
    return render_to_response("polls/poll_view.html",
        { 'poll': poll, 'categories': categories, 'category_count' : len(categories), 'breadcrumbs' : breadcrumbs },
        context_instance=RequestContext(req))

@login_required
def view_report(req, poll_id, location_id=None, as_module=False):
    template = "polls/poll_report.html"
    poll = get_object_or_404(Poll, pk=poll_id)
    try:
        response_rate =  poll.responses.distinct().count()* 100.0 / poll.contacts.distinct().count()
    except ZeroDivisionError:
        response_rate="N/A"
    if as_module:
        if poll.type == Poll.TYPE_TEXT:
            template = "polls/poll_report_text.html"
        elif poll.type == Poll.TYPE_NUMERIC:
            template = "polls/poll_report_numeric.html"

    report_function = None
    is_text_poll = True
    if Poll.TYPE_CHOICES[poll.type]['db_type'] == Attribute.TYPE_TEXT:
        report_function = poll.responses_by_category
    elif Poll.TYPE_CHOICES[poll.type]['db_type'] == Attribute.TYPE_FLOAT:
        report_function = poll.get_numeric_report_data
        is_text_poll = False

    if location_id:
        locations = get_object_or_404(Location, pk=location_id)
        locations = [locations, ]
    else:
        #locations = Location.tree.root_nodes().order_by('name') # need to find compatable simple_locations
        locations = Location.tree.all().order_by('name')

    results = []

    for location in locations:
        report = report_function(location=location, for_map=False)

        if len(report):
            if is_text_poll:
                offset = 0
                while (offset < len(report)):
                    #reset the current row
                    row = {'location_name':report[offset]['location_name'],
                           'location_id':report[offset]['location_id']}
                    data = []
                    total = 0.0

                    for c in poll.categories.order_by('name'):
                        if  offset < len(report) and \
                            report[offset]['location_id'] == row['location_id'] and \
                            report[offset]['category__name'] == c.name:
                                total += report[offset]['value']
                                data.append((report[offset]['category__name'],
                                             report[offset]['category__color'],
                                             report[offset]['value'],))
                                offset += 1
                        else:
                            data.append((c.name, c.color, 0,))
                    if  offset < len(report) and \
                        report[offset]['location_id'] == row['location_id'] and \
                        report[offset]['category__name'] == 'uncategorized':
                            total += report[offset]['value']
                            data.append((report[offset]['category__name'],
                                         report[offset]['category__color'],
                                         report[offset]['value'],))
                            offset += 1
                    else:
                        data.append(('uncategorized', '', 0,))
                    percent_data = []
                    for d in data:
                        percent_data.append((d + (d[2] * 100.0 / total,)))
                    row['report_data'] = percent_data
                    results.append(row)
            elif Poll.TYPE_CHOICES[poll.type]['db_type'] == Attribute.TYPE_FLOAT:
                results = results + list(report)

    breadcrumbs = (('Polls', reverse('polls')),)
    context = { 'poll':poll, 'breadcrumbs':breadcrumbs, 'categories':poll.categories.order_by('name'), 'report_rows':results, 'response_rate':response_rate }

    if poll.type != Poll.TYPE_TEXT and poll.type != Poll.TYPE_NUMERIC:
        return render_to_response(
        "polls/poll_index.html",
        { 'polls': Poll.objects.order_by('start_date'), 'breadcrumbs': (('Polls', ''),) },
        context_instance=RequestContext(req))
    else:
        return render_to_response(template, context, context_instance=RequestContext(req))

@login_required
@cache_control(no_cache=True, max_age=0)
def view_poll_details(req, form_id):
    poll = get_object_or_404(Poll.objects.annotate(Count('contacts')), pk=form_id)
    return render_to_response("polls/poll_details.html",
        { 'poll': poll },
        context_instance=RequestContext(req))

@login_required
@permission_required('poll.can_edit_poll')
def edit_poll(req, poll_id):
    poll = get_object_or_404(Poll, pk=poll_id)
    categories = Category.objects.filter(poll=poll)

    breadcrumbs = (('Polls', reverse('polls')), ('Edit Poll', ''))

    if req.method == 'POST':
        form = EditPollForm(req.POST, instance=poll)
        if form.is_valid():
            poll = form.save()
            poll.contacts = form.cleaned_data['contacts']
            return render_to_response("polls/poll_details.html",
                {"poll" : poll},
                context_instance=RequestContext(req))
    else:
        form = EditPollForm(instance=poll)

    return render_to_response("polls/poll_edit.html",
        { 'form': form, 'poll': poll, 'categories': categories, 'category_count' : len(categories), 'breadcrumbs' : breadcrumbs },
        context_instance=RequestContext(req))

@login_required
def view_responses(req, poll_id, as_module=False):
    poll = get_object_or_404(Poll, pk=poll_id)

    responses = poll.responses.all().order_by('-date')
    print responses.count()
    breadcrumbs = (('Polls', reverse('polls')), ('Responses', ''))

    template = "polls/responses.html"
    if as_module:
        template = "polls/response_table.html"

    typedef = Poll.TYPE_CHOICES[poll.type]
    return render_to_response(template,
        { 'poll': poll, 'responses': responses, 'breadcrumbs': breadcrumbs, 'columns': typedef['report_columns'], 'db_type': typedef['db_type'], 'row_template':typedef['view_template']},
        context_instance=RequestContext(req))

def stats(req, poll_id, location_id=None):
    poll = get_object_or_404(Poll, pk=poll_id)
    location = None
    if location_id:
        location = get_object_or_404(Location, pk=location_id)
    json_response_data = {}
    json_response_data = {'layer_title':'Survey:%s' % poll.name, 'layer_type':'categorized', 'data':list(poll.responses_by_category(location))}
    return HttpResponse(mark_safe(simplejson.dumps(json_response_data)))

def number_details(req, poll_id):
    poll = get_object_or_404(Poll, pk=poll_id)
    return HttpResponse(mark_safe(simplejson.dumps(list(poll.get_numeric_detailed_data()))))

def _get_response_edit_form(response, data=None):
    typedef = Poll.TYPE_CHOICES[response.poll.type]
    form = None
    if typedef['edit_form']:
        form = typedef['edit_form']
        if type(form) == str:
            m = '.'.join(form.split('.')[:-1])
            klass = form.split('.')[-1]
            module = __import__(module, globals(), locals(), [klass])
            form = getattr(module, klass)
    else:
        parser = typedef['parser']
        class CustomForm(forms.Form):
            def __init__(self, data=None, **kwargs):
                response = kwargs.pop('response')
                if data:
                    forms.Form.__init__(self, data, **kwargs)
                else:
                    forms.Form.__init__(self, **kwargs)

            value = forms.CharField()
            def clean(self):
                cleaned_data = self.cleaned_data
                value = cleaned_data.get('value')
                try:
                    cleaned_data['value'] = parser(value)
                except ValidationError as e:
                    if getattr(e, 'messages', None):
                        self._errors['value'] = self.error_class([str(e.messages[0])])
                    else:
                        self._errors['value'] = self.error_class([u"Invalid value"])
                    del cleaned_data['value']
                return cleaned_data
        form = CustomForm

    if data:
        return form(data, response=response)
    else:
        value = None
        if not typedef['edit_form']:
            value = response.message.text
        elif typedef['db_type'] == Attribute.TYPE_TEXT:
            value = response.eav.poll_text_value
        elif typedef['db_type'] == Attribute.TYPE_FLOAT:
            value = response.eav.poll_number_value
        elif typedef['db_type'] == Attribute.TYPE_OBJECT:
            value = response.eav.poll_location_value
        return form(response=response, initial={'value':value})

@login_required
@permission_required('poll.can_edit_poll')
def apply_response(req, response_id):
    response = get_object_or_404(Response, pk=response_id)
    poll = response.poll
    if poll.type == Poll.TYPE_REGISTRATION:
        try:
            response.message.connection.contact.name = response.eav.poll_text_value
            response.message.connection.contact.save()
        except AttributeError:
            pass
    elif poll.type == Poll.TYPE_LOCATION:
        try:
            response.message.connection.contact.reporting_location = response.eav.poll_location_value
            response.message.connection.contact.save()
        except AttributeError:
            pass

    return redirect(reverse('poll-responses', args=[poll.pk]))

@login_required
def apply_all(req, poll_id):
    poll = get_object_or_404(Poll, pk=poll_id)
    for response in Response.objects.filter(poll=poll):
        if poll.type == Poll.TYPE_REGISTRATION:
            try:
                response.message.connection.contact.name = response.eav.poll_text_value
                response.message.connection.contact.save()
            except AttributeError:
                pass
        elif poll.type == Poll.TYPE_LOCATION:
            try:
                response.message.connection.contact.reporting_location = response.eav.poll_location_value
                response.message.connection.contact.save()
            except AttributeError:
                pass
    return redirect(reverse('poll-responses', args=[poll.pk]))

@login_required
@transaction.commit_on_success
@permission_required('poll.can_edit_poll')
def edit_response(req, response_id):
    response = get_object_or_404(Response, pk=response_id)
    poll = response.poll
    typedef = Poll.TYPE_CHOICES[poll.type]
    view_template = typedef['view_template']
    edit_template = typedef['edit_template']
    db_type = typedef['db_type']
    if req.method == 'POST':
        form = _get_response_edit_form(response, data=req.POST)
        if form.is_valid():
            if 'categories' in form.cleaned_data:
                response.update_categories(form.cleaned_data['categories'], req.user)

            if 'value' in form.cleaned_data:
                if db_type == Attribute.TYPE_FLOAT:
                    response.eav.poll_number_value = form.cleaned_data['value']
                elif db_type == Attribute.TYPE_OBJECT:
                    response.eav.poll_location_value = form.cleaned_data['value']
                elif db_type == Attibute.TYPE_TEXT:
                    response.eav.poll_text_value = form.cleaned_data['value']
            response.save()
            return render_to_response(view_template,
                { 'response' : response, 'db_type':db_type },
                context_instance=RequestContext(req))
        else:
            return render_to_response(edit_template,
                            { 'response' : response, 'form':form, 'db_type':db_type },
                            context_instance=RequestContext(req))
    else:
        form = _get_response_edit_form(response)

    return render_to_response(edit_template,
        { 'form' : form, 'response': response, 'db_type':db_type },
        context_instance=RequestContext(req))

@login_required
def view_response(req, response_id):
    response = get_object_or_404(Response, pk=response_id)
    db_type = Poll.TYPE_CHOICES[response.poll.type]['db_type']
    view_template = Poll.TYPE_CHOICES[response.poll.type]['view_template']
    return render_to_response(view_template,
        { 'response': response, 'db_type': db_type},
        context_instance=RequestContext(req))

@login_required
@permission_required('poll.can_edit_poll')
def delete_response (req, response_id):
    response = get_object_or_404(Response, pk=response_id)
    poll = response.poll
    if req.method == 'POST':
        response_message=response.message
        response_message.application=None
        response_message.save()
        response.delete()

    return HttpResponse(status=200)

@login_required
def view_category(req, poll_id, category_id):
    poll = get_object_or_404(Poll, pk=poll_id)
    category = get_object_or_404(Category, pk=category_id)
    return render_to_response("polls/category_view.html",
        { 'poll': poll, 'category' : category },
        context_instance=RequestContext(req))

@login_required
@transaction.commit_on_success
@permission_required('poll.can_edit_poll')
def edit_category (req, poll_id, category_id):
    poll = get_object_or_404(Poll, pk=poll_id)
    category = get_object_or_404(Category, pk=category_id)
    if req.method == 'POST':
        form = CategoryForm(req.POST, instance=category)

        if form.is_valid():
            if form.cleaned_data['default'] == True:
                Category.clear_defaults(poll)
            category = form.save(commit=False)
            category.poll = poll
            category.save()
            return render_to_response("polls/category_view.html",
                { 'form' : form, 'poll': poll, 'category' : category },
                context_instance=RequestContext(req))
        else:
            return render_to_response("polls/category_edit.html",
                            { 'form' : form, 'poll': poll, 'category' : category },
                            context_instance=RequestContext(req))
    else:
        form = CategoryForm(instance=category)

    return render_to_response("polls/category_edit.html",
        { 'form' : form, 'poll': poll, 'category' : category },
        context_instance=RequestContext(req))

@login_required
@permission_required('poll.can_edit_poll')
def add_category(req, poll_id):
    poll = get_object_or_404(Poll, pk=poll_id)
    form = CategoryForm()

    if req.method == 'POST':
        form = CategoryForm(req.POST)
        if form.is_valid():
            if form.cleaned_data['default'] == True:
                for c in Category.objects.filter(poll=poll, default=True):
                    c.default = False
                    c.save()
            category = form.save(commit=False)
            category.poll = poll
            category.save()
            poll.categories.add(category)
            return render_to_response("polls/category_view.html",
                { 'category' : category, 'form' : form, 'poll' : poll },
                context_instance=RequestContext(req))
    else:
        form = CategoryForm()

    return render_to_response("polls/category_edit.html",
        { 'form' : form, 'poll' : poll },
        context_instance=RequestContext(req))

@login_required
@permission_required('poll.can_edit_poll')
def delete_poll (req, poll_id):
    poll = get_object_or_404(Poll, pk=poll_id)
    if req.method == 'POST':
        poll.delete()

    return HttpResponse(status=200)

@login_required
@permission_required('poll.can_poll')
def start_poll (req, poll_id):
    poll = Poll.objects.get(pk=poll_id)
    if req.method == 'POST':
        poll.start()

    return render_to_response("polls/poll_details.html",
        {"poll" : poll},
        context_instance=RequestContext(req))

@login_required
@permission_required('poll.can_edit_poll')
def end_poll (req, poll_id):
    poll = Poll.objects.get(pk=poll_id)
    if req.method == 'POST':
        poll.end()

    return render_to_response("polls/poll_details.html",
        {"poll" : poll},
        context_instance=RequestContext(req))

@login_required
@permission_required('poll.can_edit_poll')
def delete_category (req, poll_id, category_id):
    poll = get_object_or_404(Poll, pk=poll_id)
    category = get_object_or_404(Category, pk=category_id)

    if req.method == 'POST':
        category.delete()
    return HttpResponse(status=200)

@login_required
@permission_required('poll.can_edit_poll')
def edit_rule(req, poll_id, category_id, rule_id) :

    poll = get_object_or_404(Poll, pk=poll_id)
    category = get_object_or_404(Category, pk=category_id)
    rule = get_object_or_404(Rule, pk=rule_id)

    if req.method == 'POST':
        form = RuleForm(req.POST, instance=rule)
        if form.is_valid():
            rule = form.save(commit=False)
            rule.update_regex()
            rule.save()
            poll.reprocess_responses()
            return render_to_response("polls/rule_view.html",
                {  'rule' : rule, 'poll' : poll, 'category' : category },
                context_instance=RequestContext(req))
        else:
            return render_to_response("polls/rule_edit.html",
                { 'rule' : rule, 'form' : form, 'poll' : poll, 'category' : category },
                context_instance=RequestContext(req))
    else:
        form = RuleForm(instance=rule)

    return render_to_response("polls/rule_edit.html",
        { 'form' : form, 'poll': poll, 'category' : category, 'rule' : rule },
        context_instance=RequestContext(req))

@login_required
@permission_required('poll.can_edit_poll')
def add_rule(req, poll_id, category_id):
    poll = get_object_or_404(Poll, pk=poll_id)
    if poll.type != Poll.TYPE_TEXT:
        return HttpResponse(status=404)
    category = get_object_or_404(Category, pk=category_id)
    form = RuleForm()

    if req.method == 'POST':
        form = RuleForm(req.POST)
        if form.is_valid():
            rule = form.save(commit=False)
            rule.category = category
            rule.update_regex()
            rule.save()
            poll.reprocess_responses()
            return render_to_response("polls/rule_view.html",
                {  'rule' : rule, 'form' : form, 'poll' : poll, 'category' : category },
                context_instance=RequestContext(req))
    else:
        form = RuleForm()

    return render_to_response("polls/rule_edit.html",
        { 'form' : form, 'poll': poll, 'category' : category },
        context_instance=RequestContext(req))

@login_required
def view_rule(req, poll_id, category_id, rule_id) :

    poll = get_object_or_404(Poll, pk=poll_id)
    category = get_object_or_404(Category, pk=category_id)
    rule = get_object_or_404(Rule, pk=rule_id)
    return render_to_response("polls/rule_view.html",
        { 'rule' : rule, 'poll' : poll, 'category' : category },
        context_instance=RequestContext(req))

@login_required
def view_rules(req, poll_id, category_id):
    poll = get_object_or_404(Poll, pk=poll_id)
    category = get_object_or_404(Category, pk=category_id)
    rules = Rule.objects.filter(category=category)

    breadcrumbs = (('Polls', reverse('polls')), (poll.name, reverse("poll.views.view_poll", args=[poll.pk])), ("Categories", ''))

    return render_to_response("polls/rules.html",
        {  'poll' : poll, 'category' : category, 'rules' : rules, 'breadcrumbs': breadcrumbs },
        context_instance=RequestContext(req))

@login_required
@transaction.commit_on_success
@permission_required('poll.can_edit_poll')
def delete_rule (req, poll_id, category_id, rule_id):
    rule = get_object_or_404(Rule, pk=rule_id)
    category = rule.category
    if req.method == 'POST':
        rule.delete()
    category.poll.reprocess_responses()
    return HttpResponse(status=200)

def create_translation(request):
    translation_form=PollTranslation()
    if request.method == 'POST':
        translation_form = PollTranslation(request.POST)
        if translation_form.is_valid():
            translation_form.save()
            return HttpResponse("/fla")
    return render_to_response('polls/translation.html', dict(translation_form=translation_form),
            context_instance=RequestContext(request))



def append_msg_row(table,message):
    make_friendly = {'I': 'Incoming', "O": "Outgoing", "Q": "Queued", "S":"Sent",
                     "H": "Received"}
    table.append("<tr><td>")
    table.append(message.text)
    table.append("</td><td>")
    table.append(make_friendly[message.direction])
    table.append("</td><td>")
    table.append("%(name)s <br /> <a href=\"#\" onclick=\"javascript:reply('%(identity)s')\">%(identity)s</a>" \
                                                                    % { 'identity': message.connection.identity,
                                                                        'name': message.connection.name,})
    table.append("</td><td>")
    table.append(make_friendly[message.status])
    table.append("</td><td>")
    table.append(message.date.strftime("%m/%d/%Y %H:%m"))
    table.append("</td></tr>")


def read_only_message_table(messages,titles):
    table =[u"<table>"]
    table.append(u"\t<thead>\n\t\t<tr>")

    for item in titles:
        table.append("<th>")
        table.append(item)
        table.append("</th>")
    table.append('\t\t</tr>\n\t</thead>')

    table.append('\t<tbody>')

    for message in messages:
        append_msg_row(table,message)

    table.append(u'\t</tbody>\n</table>')
    return u"".join(table)
