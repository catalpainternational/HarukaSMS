#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4
# encoding=utf-8

import os

# -------------------------------------------------------------------- #
#                          MAIN CONFIGURATION                          #
# -------------------------------------------------------------------- #


# you should configure your database here before doing any real work.
# see: http://docs.djangoproject.com/en/dev/ref/settings/#databases
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "haruka.db",
    }
}

# debug mode is turned on as default, since rapidsms is under heavy
# development at the moment, and full stack traces are very useful
# when reporting bugs. don't forget to turn this off in production.
DEBUG = TEMPLATE_DEBUG = True


# the rapidsms backend configuration is designed to resemble django's
# database configuration, as a nested dict of (name, configuration).
#
# the ENGINE option specifies the module of the backend; the most common
# backend types (for a GSM modem or an SMPP server) are bundled with
# rapidsms, but you may choose to write your own.
#
# all other options are passed to the Backend when it is instantiated,
# to configure it. see the documentation in those modules for a list of
# the valid options for each.
INSTALLED_BACKENDS = {
#    "TLS-TT-Bluetooth": {
#        "ENGINE": "rapidsms.backends.gsm",
#        "PORT": "/dev/tty.Nokia6230-COM1",
#        'PORT' : "/dev/tty.usbmodem641",
#        "baudrate": 115200,
#        "rtscts": 1,
#  },
#    "TLS-TT": {
#        "ENGINE": "rapidsms.backends.gsm",
#        #"PORT": "/dev/tty.MTCBA-U-G410",
#        "PORT" : "/dev/tty.HUAWEIMobile-Modem",
#        "baudrate": 115200,
#        "rtscts": 1,
#  },
    "message_tester": {
        "ENGINE": "rapidsms.backends.bucket",
    }
}

DEFAULT_BACKEND_NAME = "console"

# to help you get started quickly, many django/rapidsms apps are enabled
# by default. you may wish to remove some and/or add your own.
INSTALLED_APPS = [
    "haruka_theme",
    # the essentials.
    "django_nose",
    "djtables",
    "rapidsms",

    # common dependencies (which don't clutter up the ui).
    "rapidsms.contrib.handlers",

    # enable the django admin using a little shim app (which includes
    # the required urlpatterns), and a bunch of undocumented apps that
    # the AdminSite seems to explode without.
    "django.contrib.sites",
    "django.contrib.auth",
    "django.contrib.admin",
    "django.contrib.sessions",
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",

    # the rapidsms contrib apps.
    "rapidsms.contrib.default",
    "rapidsms.contrib.export",
    "rapidsms.contrib.locations",
    "rapidsms.contrib.messaging",
    "rapidsms.contrib.scheduler",
    "rapidsms.contrib.echo",

    # Haruka specific #
    ###################
    # 'rosetta',
    "eav", # used by xforms
    "uni_form", # used by xforms
    "django_sorting", # used by groups
    "pagination",
    "rapidsms_xforms",
    "registration",
    "contact",
    'groups',
    "bulksend",

    # for the polls
    "mptt",
    "code_generator",
    "rapidsms.contrib.locations.nested",
    "simple_locations",
    "rapidsms_httprouter",
    "poll",

]

if DEBUG == True:
    INSTALLED_APPS += [
        "django_extensions",
        "werkzeug",
    ]
elif DEBUG == False:
    INSTALLED_APPS += [
        "django_wsgiserver"
    ]


# rapidsms-httprouter related items
SMS_APPS = [
    "registration",
    "rapidsms_xforms",
    "bulksend",
    "poll",
]

# pointing the rapidsms-httprouter to pygsm-gateway
ROUTER_URL = "http://localhost:8080/?backend=%(backend)s&identity=%(recipient)s&text=%(text)s"
ROUTER_ADDR = "http://localhost:8080/"


# rapidsms-xforms specific settings
XFORMS_HOST = 'localhost:8000'


# this rapidsms-specific setting defines which views are linked by the
# tabbed navigation. when adding an app to INSTALLED_APPS, you may wish
# to add it here, also, to expose it in the rapidsms ui.
RAPIDSMS_TABS = [
    # Haruka specific
    ('rapidsms-dashboard',                                  "Activity"),
    ("polls",                                               "Polls"),
    ("xforms",                                              "Data Collection"),
    ("bulksend",                                            "Messaging"),
    ('list-groups',                                         "Groups"),
    ("registration",                                        "Contacts"),
#    ("httprouter-console",                                  "Testing"), # for use with rapidsms_httprouter
#    ("rapidsms.contrib.messagelog.views.message_log",       "Message Log"), # can't be used with rapidsms_httprouter
#    ("rapidsms.contrib.messaging.views.messaging",          "Messaging"),
#    ("rapidsms.contrib.locations.views.locations",          "Map"),
#    ("rapidsms.contrib.scheduler.views.index",              "Event Scheduler"),
#    ("rapidsms.contrib.httptester.views.generate_identity", "Message Tester"),
]


MIDDLEWARE_CLASSES = (
    'django_sorting.middleware.SortingMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',

#    'django.middleware.csrf.CsrfViewMiddleware',
#    'django.middleware.csrf.CsrfResponseMiddleware',
)


# -------------------------------------------------------------------- #
#                         BORING CONFIGURATION                         #
# -------------------------------------------------------------------- #


# after login (which is handled by django.contrib.auth), redirect to the
# dashboard rather than 'accounts/profile' (the default).
LOGIN_REDIRECT_URL = "/"
LOGIN_URL = "/account/login"

# use django-nose to run tests. rapidsms contains lots of packages and
# modules which django does not find automatically, and importing them
# all manually is tiresome and error-prone.
TEST_RUNNER = "django_nose.NoseTestSuiteRunner"


# for some reason this setting is blank in django's global_settings.py,
# but it is needed for static assets to be linkable.
MEDIA_URL = "/site-media/"


# this is required for the django.contrib.sites tests to run, but also
# not included in global_settings.py, and is almost always ``1``.
# see: http://docs.djangoproject.com/en/dev/ref/contrib/sites/
SITE_ID = 1


# the default log settings are very noisy.
LOG_LEVEL = "INFO" # was "DEBUG"
LOG_FILE = "logs/rapidsms.log"
LOG_FORMAT = "[%(name)s]: %(message)s"
LOG_SIZE = 8192  # 8192 bits = 8 kb
LOG_BACKUPS = 256  # number of logs to keep


# these weird dependencies should be handled by their respective apps,
# but they're not, so here they are. most of them are for django admin.
TEMPLATE_CONTEXT_PROCESSORS = [
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.request",
    "django.core.context_processors.static",
]

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT =  os.getcwd()+'/static/'

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    #'django.template.loaders.eggs.Loader',
)

# -------------------------------------------------------------------- #
#                           HERE BE DRAGONS!                           #
#        these settings are pure hackery, and will go away soon        #
# -------------------------------------------------------------------- #


# these apps should not be started by rapidsms in your tests, however,
# the models and bootstrap will still be available through django.
TEST_EXCLUDED_APPS = [
    "django.contrib.sessions",
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "rapidsms",
    #"rapidsms.contrib.ajax", # can't be used with rapidsms_httprouter
    #"rapidsms.contrib.httptester", # can't be used with rapidsms_httprouter
]

# the project-level url patterns
ROOT_URLCONF = "urls"

# set Language default
LANGUAGE_CODE = 'en-us'
COUNTRY_CODE = 'TL'
#COUNTRY_CODE = 'US'


# since we might hit the database from any thread during testing, the
# in-memory sqlite database isn't sufficient. it spawns a separate
# virtual database for each thread, and syncdb is only called for the
# first. this leads to confusing "no such table" errors. We create
# a named temporary instance instead.
import os
import tempfile
import sys

if 'test' in sys.argv:
    for db_name in DATABASES:
        DATABASES[db_name]['TEST_NAME'] = os.path.join(
            tempfile.gettempdir(),
            "%s.rapidsms.test.sqlite3" % db_name)
