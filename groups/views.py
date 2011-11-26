import logging

from django import forms
from django.http import HttpResponse
from django.shortcuts import redirect, render_to_response, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.utils.translation import ugettext_lazy as _
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.db.models import Count
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.contrib import messages

from rapidsms.models import Contact

from groups.models import Group
from groups.forms import GroupForm, ContactForm



@login_required
def list_groups(request):
    groups = Group.objects.annotate(count=Count('contacts'))
    context = {
        'groups': groups.order_by('name'),
    }
    return render_to_response('groups/groups/list.html', context,
                              context_instance=RequestContext(request))


@login_required
@transaction.commit_on_success
def create_edit_group(request, group_id=None):
    group = None
    if group_id:
        group = get_object_or_404(Group, pk=group_id)
        if not group.is_editable:
            return HttpResponseForbidden('Access denied')
    if request.method == 'POST':
        form = GroupForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
            messages.info(request, "Group saved successfully")
            return HttpResponseRedirect(reverse('list-groups'))
    else:
        form = GroupForm(instance=group)
    context = {
        'form': form,
        'group': group,
    }
    return render_to_response('groups/groups/create_edit.html', context,
                              context_instance=RequestContext(request))


@login_required
@transaction.commit_on_success
def delete_group(request, group_id):
    group = get_object_or_404(Group, pk=group_id)
    if not group.is_editable:
        return HttpResponseForbidden('Access denied')
    if request.method == 'POST':
        group.delete()
        messages.info(request, 'Group successfully deleted')
        return HttpResponseRedirect(reverse('list-groups'))
    context = {'group': group}
    return render_to_response('groups/groups/delete.html', context,
                              RequestContext(request))


@login_required
def list_contacts(request):
    contacts = Contact.objects
    context = {
        'contacts': contacts.order_by('name'),
    }
    return render_to_response('groups/contacts/list.html', context,
                              context_instance=RequestContext(request))


@login_required
@transaction.commit_on_success
def create_edit_contact(request, contact_id=None):
    contact = None
    if contact_id:
        contact = get_object_or_404(Contact, pk=contact_id)
    if request.method == 'POST':
        form = ContactForm(request.POST, instance=contact)
        if form.is_valid():
            form.save()
            messages.info(request, "Contact saved successfully")
            return HttpResponseRedirect(reverse('list-contacts'))
    else:
        form = ContactForm(instance=contact)
    context = {
        'form': form,
        'contact': contact,
    }
    return render_to_response('groups/contacts/create_edit.html', context,
                              context_instance=RequestContext(request))


@login_required
@transaction.commit_on_success
def delete_contact(request, contact_id):
    contact = get_object_or_404(Contact, pk=contact_id)
    if request.method == 'POST':
        contact.delete()
        messages.info(request, 'Contact successfully deleted')
        return HttpResponseRedirect(reverse('list-contacts'))
    context = {'contact': contact}
    return render_to_response('groups/contacts/delete.html', context,
                              RequestContext(request))
