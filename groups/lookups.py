from django.http import HttpResponse
from django.utils import simplejson
from django.core.serializers import json

from selectable.base import ModelLookup
from selectable.registry import registry

from rapidsms.models import Contact


class ContactLookup(ModelLookup):
    model = Contact
    filters = {}
    search_field = 'name__icontains'

    def results(self, request):
        term = request.GET.get('term', '')
        raw_data = self.get_query(request, term)[:10]
        data = []
        for item in raw_data:
            data.append(self.format_item(item))
        content = simplejson.dumps(data, cls=json.DjangoJSONEncoder,
                                   ensure_ascii=False)
        return HttpResponse(content, content_type='application/json')    

registry.register(ContactLookup)
