from django.contrib import admin
from .models import Poll, Response, Category, Rule, ResponseCategory,Translation

admin.site.register(Poll)
admin.site.register(Response)
admin.site.register(Category)
admin.site.register(Rule)
admin.site.register(ResponseCategory)
admin.site.register(Translation)


