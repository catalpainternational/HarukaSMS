import logging
import re

from django import forms

from groups.models import Group
from groups.utils import format_number
from groups.validators import validate_phone


from rapidsms.models import Contact, Backend


__all__ = ('GroupForm', 'ContactForm', 'ForwardingRuleFormset',)


logger = logging.getLogger('groups.forms')


class FancyPhoneInput(forms.TextInput):

    def render(self, name, value, attrs=None):
        if value:
            value = format_number(value)
        return super(FancyPhoneInput, self).render(name, value, attrs)

    def value_from_datadict(self, data, files, name):
        value = super(FancyPhoneInput, self).value_from_datadict(data, files, name)
        if value:
            value = re.sub(r'\D', '', value)
        return value


from django.contrib.admin.widgets import FilteredSelectMultiple
from django.forms import ModelForm
from django import forms

class GroupForm(forms.ModelForm):

    contacts=forms.ModelMultipleChoiceField(Contact.objects.all(),widget=FilteredSelectMultiple("Contacts",False,attrs={'rows':'10'}))

    class Meta:
        model = Group
        exclude = ('is_editable',)

    def __init__(self, *args, **kwargs):
        super(GroupForm, self).__init__(*args, **kwargs)
        qs = Contact.objects.order_by('name')
        self.fields['contacts'].help_text = ''
        qs = Contact.objects.order_by('name')
        self.fields['contacts'].queryset = qs
        self.fields['contacts'].widget.attrs['class'] = 'horitzonal-multiselect'
        print self.fields['contacts'].widget

class ContactForm(forms.ModelForm):
    """ Form for managing contacts """

    groups = forms.ModelMultipleChoiceField(queryset=Group.objects.none())
    phone = forms.CharField(validators=[validate_phone], required=True, widget=FancyPhoneInput)

    class Meta:
        model = Contact
        exclude = ('language', 'name', 'primary_backend', 'pin')

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance')
        if instance and instance.pk:
            pks = instance.groups.values_list('pk', flat=True)
            kwargs['initial'] = {'groups': list(pks)}
        super(ContactForm, self).__init__(*args, **kwargs)
        self.fields['groups'].widget = forms.CheckboxSelectMultiple()
        self.fields['groups'].queryset = Group.objects.order_by('name')
        self.fields['groups'].required = False
        for name in ('first_name', 'last_name', 'phone'):
            self.fields[name].required = True

    def save(self, commit=True):
        instance = super(ContactForm, self).save()
        instance.groups = self.cleaned_data['groups']
        return instance
