#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.conf.urls.defaults import *
from . import views


urlpatterns = patterns('',

    url(r'^$',		#TODO: Review this to see if we still use this pattern
        views.registration,
        name="registration"),

    url(r'^registration/$',
        views.registration,
        name="registration"),

    url(r'^registration/(?P<pk>\d+)/edit/$',
        views.registration,
        name="registration_edit"),
)
