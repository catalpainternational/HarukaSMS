from django import forms

#from django.contrib.auth.models import Group
from .models import Poll, Category, Rule ,Translation
from rapidsms.models import Contact
from groups.models import Group
from django.forms.widgets import RadioSelect

import re


class ReplyForm(forms.Form):
    recipient = forms.CharField(max_length=20)
    message = forms.CharField(max_length=160, widget=forms.TextInput(attrs={'size':'60'}))


class NewPollForm(forms.Form): # pragma: no cover

    TYPE_YES_NO = 'yn'
    choices = [(choice['type'], choice['label']) for choice in Poll.TYPE_CHOICES.values()]
    choices.append((TYPE_YES_NO, 'Yes/No Question'))

    poll_type = forms.ChoiceField(
               required=True,
               choices=tuple(choices)
               )
    response_type=forms.ChoiceField(choices=Poll.RESPONSE_TYPE_CHOICES,widget=RadioSelect,initial=Poll.RESPONSE_TYPE_ALL)

    def updateTypes(self):
        self.fields['poll_type'].widget.choices = [(NewPollForm.TYPE_YES_NO, 'Yes/No Question')]
        self.fields['poll_type'].widget.choices += [(choice['type'], choice['label']) for choice in Poll.TYPE_CHOICES.values()]

    name = forms.CharField(max_length=32, required=True)
    question = forms.CharField(max_length=160, required=True, widget=forms.Textarea())
    question_luo = forms.CharField(max_length=160, required=False, widget=forms.Textarea())
    default_response = forms.CharField(max_length=160, required=False, widget=forms.Textarea())
    default_response_luo = forms.CharField(max_length=160, required=False, widget=forms.Textarea())
    start_immediately = forms.BooleanField(required=False)
    contacts = forms.ModelMultipleChoiceField(queryset=Contact.objects.all(), required=False)
    groups = forms.ModelMultipleChoiceField(queryset=Group.objects.all(), required=False)

    # This may seem like a hack, but this allows time for the Contact model
    # to optionally have groups (i.e., poll doesn't explicitly depend on the rapidsms-auth
    # app.
    #def __init__(self, data=None, **kwargs):
    #    if data:
    #        forms.Form.__init__(self, data, **kwargs)
    #    else:
    #        forms.Form.__init__(self, **kwargs)
    #    if hasattr(Contact, 'groups'):
    #        self.fields['groups'] = forms.ModelMultipleChoiceField(queryset=Group.objects.all(), required=False)

    def clean(self):
        cleaned_data = self.cleaned_data
        contacts = cleaned_data.get('contacts')
        groups = cleaned_data.get('groups')
        cleaned_data['question'] = cleaned_data.get('question').replace('%', u'\u0025')
        if 'default_response' in cleaned_data:
            cleaned_data['default_response'] = cleaned_data['default_response'].replace('%', u'\u0025')

        if not contacts and not groups:
            raise forms.ValidationError("You must provide a set of recipients (either a group or a contact)")

        return cleaned_data

class PollTranslation(forms.ModelForm):
    class Meta:
        model = Translation
class EditPollForm(forms.ModelForm): # pragma: no cover
    class Meta:
        model = Poll
        fields = ('name', 'default_response')

    def clean(self):
        cleaned_data = self.cleaned_data
        cleaned_data['default_response'] = cleaned_data.get('default_response').replace('%', u'\u0025')
        return cleaned_data

    # This may seem like a hack, but this allows time for the Contact model's
    # default manage to be replaced at run-time.  There are many applications
    # for that, such as filtering contacts by site_id (as is done in the
    # authsites app, see github.com/daveycrockett/authsites).
    # This does, however, also make the polling app independent of authsites.
    def __init__(self, data=None, **kwargs):
        if data:
            forms.ModelForm.__init__(self, data, **kwargs)
        else:
            forms.ModelForm.__init__(self, **kwargs)
        if 'instance' in kwargs:
            self.fields['contacts'] = forms.ModelMultipleChoiceField(queryset=Contact.objects.all(), initial=kwargs['instance'].contacts.all())
        else:
            self.fields['contacts'] = forms.ModelMultipleChoiceField(queryset=Contact.objects.all())

class CategoryForm(forms.ModelForm):
    name = forms.CharField(max_length=50, required=True)
    default = forms.BooleanField(required=False)
    response = forms.CharField(max_length=160, required=False)
    priority = forms.IntegerField(required=False, widget=forms.Select(
            choices=tuple([('', '---')] + [(i, "%d" % i) for i in range(1, 11)])))
    color = forms.CharField(required=False, max_length=6, widget=forms.Select(choices=(
                (None, '---'),
                ('ff9977', 'red'),
                ('99ff77', 'green'),
                ('7799ff', 'blue'),
                ('ffff77', 'yellow'))))

    def clean(self):
        cleaned_data = self.cleaned_data
        cleaned_data['response'] = cleaned_data.get('response').replace('%', u'\u0025')
        return cleaned_data

    class Meta:
        model = Category
        fields = ('name', 'priority', 'color', 'default', 'response')

class RuleForm(forms.ModelForm):
    rule_string = forms.CharField(max_length=256, required=True)
    rule_type = forms.CharField(max_length=2, required=False, widget=forms.Select(choices=Rule.RULE_CHOICES))
    class Meta:
        model = Rule
        fields = ('rule_type', 'rule_string')

    def clean(self):
        cleaned_data = self.cleaned_data
        rule_string = cleaned_data.get('rule_string')
        rule_type = cleaned_data.get('rule_type')
        if rule_type == 'r':
            try:
                re.compile(rule_string)
            except:
                self._errors['rule_string'] = self.error_class([u"You must provide a valid regular expression"])
                del cleaned_data['rule_string']

        # Always return the full collection of cleaned data.
        return cleaned_data
