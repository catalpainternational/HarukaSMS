#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

#import csv

from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.db import transaction
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib import messages
from rapidsms.models import Contact
from rapidsms.models import Connection
from rapidsms.models import Backend
from rapidsms.contrib.registration.tables import ContactTable
from rapidsms.contrib.messaging.utils import send_message
from django.contrib.auth.decorators import login_required

from .forms import BulkRegistrationForm
from .forms import ContactForm
from .tables import ContactTable


DEFAULT_BACKEND_NAME = "TLS-TT"  # move to settings.py ?


@login_required
@transaction.commit_on_success
def registration(req, pk=None):
    contact = None
    backend_name = DEFAULT_BACKEND_NAME

    if pk is not None:
        contact = get_object_or_404(
            Contact, pk=pk)

    if req.method == "POST":
        if req.POST["submit"] == "Delete Contact":
            contact.delete()
            return HttpResponseRedirect(
                reverse(registration))

        elif "bulk" in req.FILES:
            # TODO use csv module
            #reader = csv.reader(open(req.FILES["bulk"].read(), "rb"))
            #for row in reader:
            for line in req.FILES["bulk"]:
                line_list = line.split(',')
                name = line_list[0].strip()
                identity = line_list[1].strip().replace('+','').replace(' ','')

                if Connection.objects.filter(identity=identity).exists():
                    messages.error(req, "You already have a contact with the phone number: %s (%s)" % (identity, name))
                    return HttpResponseRedirect(reverse(registration))

                try:
                    gender = line_list[2].strip()
                    age = line_list[3].strip()
                    location = line_list[4].strip()
                except:
                    gender = age = location = ''

                # we need this because of the groups extensions to contact and its custom save()
                language = 'en-us' # default behavior for now
                contact = Contact(name=name, phone=identity,
                                 #age=age, language=language)
                                 gender=gender, age=age, location=location, language=language)
                contact.save()

                # Get our backend or create one
                backend, created = Backend.objects.get_or_create(name=DEFAULT_BACKEND_NAME)

                connection = Connection(backend=backend, identity=identity,\
                    contact=contact)
                connection.save()

            messages.success(req, 'Thank you, you successfully added to your contacts.')

            return HttpResponseRedirect(
                reverse(registration))
        else:
            contact_form = ContactForm(
                instance=contact,
                data=req.POST)

            if contact_form.is_valid():
                contact = contact_form.save()
                contact.phone = contact.phone.replace('+','').replace(' ','')
                contact.language = 'en-us' #default behavior for now
                contact.save()

                backend, created = Backend.objects.get_or_create(name=DEFAULT_BACKEND_NAME)
                print contact,backend
                connection = Connection.objects.get_or_create(backend=backend, contact=contact)[0]
                connection.identity = contact.phone
                connection.save()

                messages.success(req, 'Thank you, you successfully updated %s : %s.' % (contact.name, contact.phone))

                return HttpResponseRedirect(
                    reverse(registration))
            else:
                bulk_form = BulkRegistrationForm()

    else:
        contact_form = ContactForm(instance=contact)
        bulk_form = BulkRegistrationForm()

    return render_to_response(
        "registration/dashboard.html", {
            "contacts_table": ContactTable(Contact.objects.all(), request=req),
            "contact_form": contact_form,
            "bulk_form": bulk_form,
            "contact": contact
        }, context_instance=RequestContext(req)
    )
