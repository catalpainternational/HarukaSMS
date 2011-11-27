# -*- coding: utf-8 -*-
import rapidsms
import datetime

from rapidsms.apps.base import AppBase
from .models import Poll
from django.db.models import Q

class App(AppBase):
    def handle (self, message):
        #import pdb; pdb.set_trace()
        # see if this contact matches any of our polls
        if (message.connection.identity):
            try:
                poll = Poll.objects.filter(contacts__connection__identity=message.connection.identity).exclude(start_date=None).filter(
                    Q(end_date=None) | (~Q(end_date=None) & Q(end_date__gt=datetime.datetime.now()))).latest(
                    'start_date')
                if poll.response_type == Poll.RESPONSE_TYPE_ONE and poll.responses.filter(
                    contact=message.connection.contact).exists():
                    old_response=poll.responses.filter(contact=message.connection.contact)[0]
                    response_obj, response_msg = poll.process_response(message)
                    if not response_obj.has_errors or old_response.has_errors:
                        old_response.delete()
                        if hasattr(message, 'db_message'):
                            db_message = message.db_message
                            db_message.handled_by = 'poll'
                            db_message.save()
                        message.respond(response_msg)
                    else:
                        response_obj.delete()
                    return False
                elif poll.response_type == Poll.RESPONSE_TYPE_NO_DUPS and poll.responses.filter(
                    contact=message.connection.contact, message__text=message.text).exists():
                    return False
                else:
                    response_obj, response_msg = poll.process_response(message)
                    if hasattr(message, 'db_message'):
                        # if no other app handles this message, we want
                        # the handled_by field set appropriately,
                        # it won't since this app returns false
                        db_message = message.db_message
                        db_message.handled_by = 'poll'
                        db_message.save()
                    message.respond(response_msg)
                    # play nice, let other things handle responses
                    return False
            except Poll.DoesNotExist:
                pass

        return False