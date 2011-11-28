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
from django.forms import ValidationError


k_SMSLength = 160
k_SMSPrice = 0.08
@login_required
def review(request):
    if request.method.upper() == 'GET':
        return render_to_response(
            "bulksend/dashboard.html", {
                "groups": Group.objects.all(),
                }, context_instance=RequestContext(request)
            )

    elif request.method.upper() == 'POST':

        text = request.POST.get('message')
        group_id = request.POST.get('group_id')

        try:
            group = Group.objects.get(pk=group_id)
        except:
            messages.error(request, 'A valid Group must be selected')
            return render_to_response(
                "bulksend/dashboard.html", {
                    "groups": Group.objects.all(),
                    }, context_instance=RequestContext(request)
                )


        m_count    = ((len(text) / k_SMSLength) + 1 )
        m_price    = m_count * k_SMSPrice

        g_name     = group.name
        g_size     = group.contacts.count()

        send_price = g_size * m_price
        sms_count  = g_size * m_count


        lorem_ipsum = {
            "sms_cost": k_SMSPrice,
            "sms_length": k_SMSLength,
            "sms_count" : sms_count,
            "g_name": g_name,
            "g_size": g_size,
            "m_text": text,
            "m_length": len(text),
            "m_count":m_count,
            "send_price":send_price,
            "group":group,
            }

        import datetime
        print datetime.datetime.now()
        return render_to_response(
            "bulksend/review.html",
            lorem_ipsum,
            context_instance=RequestContext(request)
        )


@login_required
def bulksend(request):
    if request.method.upper() == 'GET':
        return render_to_response(
            "bulksend/dashboard.html", {
                "groups": Group.objects.all(),
                "sms_cost":k_SMSPrice,
                "sms_length":k_SMSLength,
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
