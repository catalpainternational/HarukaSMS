#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.contrib import messages    
from rapidsms.utils.pagination import paginated
from groups.models import Group
from . import filters
from rapidsms.contrib.ajax.utils import call_router


@login_required
def bulksend(request):
    if request.method.upper() == 'GET':
        return render_to_response(
            "bulksend/dashboard.html", {
                "groups": Group.objects.all(),
            }, context_instance=RequestContext(request)
        )
    
    elif request.method.upper() == 'POST':
        
        text = request.POST.get('message')
        group_id = request.POST.get('group_id')
        
        group = Group.objects.get(pk=group_id)
        
        import datetime
        print datetime.datetime.now()
        for contact in group.contacts.all():
            connection = contact.connection_set.all()[0]
            post = {"connection_id": unicode(connection.id), "text": text}
            call_router("messaging", "send_message", **post)
        print datetime.datetime.now()
        
        messages.success(request, 'Thank you, you successfully sent your bulk message.')        
        return render_to_response(
            "bulksend/dashboard.html", {
                "groups": Group.objects.all(),
            }, context_instance=RequestContext(request)
        )
        


