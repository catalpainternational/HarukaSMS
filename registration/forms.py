#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from django import forms
from rapidsms.models import Contact


class ContactForm(forms.ModelForm):

    instance = None

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.get('instance')
        super(ContactForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Contact
        fields = ('name', 'age', 'gender', 'phone','location',)

    def clean_phone(self):
        p = self.cleaned_data['phone']
        print "instance :", self.instance.phone
        if Contact.objects.filter(phone=p).exists() and not(self.instance and self.instance.phone == p):
            raise forms.ValidationError("You already have a contact with this phone number")
        return p

    def clean_name(self):
        n= self.cleaned_data['name']
        if n is None or len(n.strip()) == 0:
            raise forms.ValidationError("The contact name cannot be empty")
        return n.strip()

# the built-in FileField doesn't specify the 'size' attribute, so the
# widget is rendered at its default width -- which is too wide for our
# form. this is a little hack to shrink the field.
class SmallFileField(forms.FileField):
    def widget_attrs(self, widget):
        return { "size": 10 }


class BulkRegistrationForm(forms.Form):
    bulk = SmallFileField(
        label="Upload CSV file",
        required=False,
        help_text="Upload a <em>plain text file</em> " +
                  "containing a single contact per line, <br/>" +
                  "<em>firstname lastname, telephone number, gender, age, location</em> <br/>" +
                  "for example: " +
                  "Maria Soares, +6707999999, f, 34, Gleno")
