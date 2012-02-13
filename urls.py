from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from poll import views

admin.autodiscover()


urlpatterns = patterns('',

    # Uncomment the admin/doc line below to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    (r'^admin/', include(admin.site.urls)),

    # RapidSMS core URLs
    (r'^account/', include('rapidsms.urls.login_logout')),

    url(r'^$', views.dashboard, name='rapidsms-dashboard'),

    # RapidSMS contrib app URLs
    (r'^ajax/', include('rapidsms.contrib.ajax.urls')),
    (r'^export/', include('rapidsms.contrib.export.urls')),
    (r'^httptester/', include('rapidsms.contrib.httptester.urls')),
    (r'^locations/', include('rapidsms.contrib.locations.urls')),
    (r'^messagelog/', include('rapidsms.contrib.messagelog.urls')),
    (r'^messaging/', include('rapidsms.contrib.messaging.urls')),
    (r'^scheduler/', include('rapidsms.contrib.scheduler.urls')),

    # Haruka specific
    (r'^registration/', include('registration.urls')),
    (r'^groups/', include('groups.urls')),
    (r'^bulksend/', include('bulksend.urls')),
    ('', include('rapidsms_xforms.urls')),
    ('^polls/', include('poll.urls')),
    ('', include('rapidsms_httprouter.urls')),
)

urlpatterns += patterns('',
    # helper URLs file that automatically serves the 'static' folder in
    # INSTALLED_APPS via the Django static media server (NOT for use in
    # production)
    (r'^', include('rapidsms.urls.static_media')),
)
urlpatterns += staticfiles_urlpatterns()

urlpatterns += patterns('',
        url(r'^static/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.STATIC_ROOT,
        }),
   )
