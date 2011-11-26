#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from django import forms
from groups.models import Group


class BulkSend(forms.Form):
    bulk = forms.ChoiceField(widget=forms.RadioSelect, choices=(('1', 'First',), ('2', 'Second',))))
