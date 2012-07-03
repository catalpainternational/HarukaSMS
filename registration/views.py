#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

import csv

from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.db import transaction
from django.shortcuts import render_to_response, get_object_or_404
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from rapidsms.models import Contact
from rapidsms.models import Connection
from rapidsms.models import Backend

import phonenumbers

from .forms import BulkRegistrationForm
from .forms import ContactForm
from .tables import ContactTable
from settings import LANGUAGE_CODE, COUNTRY_CODE, DEFAULT_BACKEND_NAME, SANITIZE_PHONENUMBERS


@require_GET
@login_required
def contacts_as_csv(req):
    """ CSV export of all contacts """
    contacts = Contact.objects.all().order_by('name')

    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=harukasms-contacts.csv'

    writer = csv.writer(response)
    writer.writerow(['Name', 'Telephone Number', ' Gender', 'Age', 'Location'])
    for contact in contacts:
        writer.writerow([contact.name, contact.phone, contact.gender, contact.age, contact.location])
    return response


@login_required
@transaction.commit_on_success
def registration(req, pk=None):
    contact = None

    #TODO: fix case where a user registers via sms and then edits via web
    if pk is not None:
        contact = get_object_or_404(
            Contact, pk=pk)

    if req.method == "POST":
        if req.POST["submit"] == "Delete Contact":
            contact.delete()
            messages.success(req, 'You have successfully deleted a contact.')

            return HttpResponseRedirect(
                reverse(registration))

        elif "bulk" in req.FILES:
            # TODO use csv module
            #reader = csv.reader(open(req.FILES["bulk"].read(), "rb"))
            #for row in reader:
            for line in req.FILES["bulk"]:
                line_list = line.split(',')
                if line_list.__len__() >= 2:
                    name = line_list[0].strip()
                    if not name.startswith('Name'):

                        identity = line_list[1].strip()
                        if SANITIZE_PHONENUMBERS:
                            identity = phonenumbers.format_number(phonenumbers.parse(identity, COUNTRY_CODE), phonenumbers.PhoneNumberFormat.E164)
                        identity = identity.replace('+', '')  # this makes the polls app happy again

                        try:
                            gender = line_list[2].strip()
                            age = line_list[3].strip()
                            location = line_list[4].strip()
                        except:
                            gender = age = location = ''

                        if not age.isdigit():
                                age = 0

                        # Create or update our contact
                        contact, new = Contact.objects.get_or_create(connection__identity=identity)
                        contact.name = name
                        contact.phone = identity
                        contact.gender = gender
                        contact.age = age
                        contact.location = location
                        contact.language = LANGUAGE_CODE
                        contact.save()

                        # Get our backend or create one
                        backend, new = Backend.objects.get_or_create(name=DEFAULT_BACKEND_NAME)
                        connection, new = Connection.objects.get_or_create(backend=backend, identity=identity)
                        connection.contact = contact
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
                if SANITIZE_PHONENUMBERS:
                    #Sanitize and properly format the phone number
                    contact.phone = phonenumbers.format_number(phonenumbers.parse(contact.phone, COUNTRY_CODE), phonenumbers.PhoneNumberFormat.E164)
                contact.phone = contact.phone.replace('+', '')  # this makes the polls app happy again
                contact.language = LANGUAGE_CODE
                contact.save()

                backend, created = Backend.objects.get_or_create(name=DEFAULT_BACKEND_NAME)
                connection = Connection.objects.get_or_create(backend=backend, identity=contact.phone)[0]
                connection.contact = contact
                connection.identity = contact.phone
                connection.save()

                messages.success(req, 'Thank you, you successfully updated %s : %s.' % (contact.name, contact.phone))

                return HttpResponseRedirect(
                    reverse(registration))
            else:
                bulk_form = BulkRegistrationForm()

    elif req.method == "GET":
        contact_form = ContactForm(instance=contact)
        bulk_form = BulkRegistrationForm()

    contact_table = ContactTable(Contact.objects.all(), request=req)

    return render_to_response(
        "registration/dashboard.html", {
            "contacts_table": contact_table,
            "contact_form": contact_form,
            "bulk_form": bulk_form,
            "contact": contact
        }, context_instance=RequestContext(req)
    )
