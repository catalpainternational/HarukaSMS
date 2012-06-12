# -*- coding: utf-8 -*-
import rapidsms
import datetime

from rapidsms.apps.base import AppBase
from .models import Poll
from django.db.models import Q

class App(AppBase):
    def handle (self, message):
        # see if this contact matches any of our polls
        if (message.connection.identity):
            try:
                poll = Poll.objects.filter(contacts__connection__identity=message.connection.identity).exclude(start_date=None).filter(
                    Q(end_date=None) | (~Q(end_date=None) & Q(end_date__gt=datetime.datetime.now()))).latest(
                    'start_date')
                
                # accept queries for response rates with '?'
                if message.text.startswith('?'):
                    response_rate =  int(poll.responses.distinct().count()* 100.0 / poll.contacts.distinct().count())
                    response_text = "Response rate %s%%%% \n" % (response_rate,)

                    responses_by_category = poll.responses_by_category()
                    for category in responses_by_category:
                        category_rate = int(category['value'] * 100.0 / poll.contacts.distinct().count())
                        response_text = response_text + "-- %s : %s%%%% \n" % (category['category__name'], category_rate)
                    if response_text is not None and len(response_text)>0:
                        message.respond(response_text)
                    return False

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
                        if response_msg is not None:
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
                    if response_msg is not None:
                        message.respond(response_msg)
                    #else: the response msg is none, don't respond

                    # play nice, let other things handle responses
                    return False
            except Poll.DoesNotExist:
                pass

        return False