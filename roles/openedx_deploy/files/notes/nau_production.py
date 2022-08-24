# Adapted from tutor
# https://github.com/overhangio/tutor-notes/blob/283890555b01029c3e739e7e3c84719aa18c7972/tutornotes/templates/notes/apps/settings/tutor.py

import os

from .common import *

from django.core.exceptions import ImproperlyConfigured


def get_env_value(env_variable, default=None):
    try:
        return os.environ[env_variable]
    except KeyError:
        if default:
            return default
        else:
            error_msg = 'Set the {} environment variable'.format(env_variable)
            raise ImproperlyConfigured(error_msg)

SECRET_KEY = get_env_value("NOTES_SECRET_KEY")
ALLOWED_HOSTS = [
    "notes",
    get_env_value("NOTES_HOST"),
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "HOST": get_env_value("MYSQL_HOST"),
        "PORT": int(get_env_value("MYSQL_PORT")),
        "NAME": get_env_value("NOTES_MYSQL_DATABASE"),
        "USER": get_env_value("NOTES_MYSQL_USERNAME"),
        "PASSWORD": get_env_value("NOTES_MYSQL_PASSWORD"),
        "OPTIONS": {
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

CLIENT_ID = get_env_value("NOTES_OAUTH2_ID", "notes")
CLIENT_SECRET = get_env_value("NOTES_OAUTH2_SECRET")

ELASTICSEARCH_DSL = {'default': {'hosts': get_env_value("ELASTICSEARCH_HOST_PORT") }}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "": {
            "handlers": ["console"],
            "level": "INFO",
        },
    },
}
