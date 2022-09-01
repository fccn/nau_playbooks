# Adapted from tutor-discovery https://github.com/overhangio/tutor-discovery
# - https://github.com/overhangio/tutor-discovery/blob/84886feaa76e91b0c725566cef503dd2d215979c/tutordiscovery/templates/discovery/apps/settings/tutor/production.py
# - https://github.com/overhangio/tutor-discovery/blob/84886feaa76e91b0c725566cef503dd2d215979c/tutordiscovery/templates/discovery/apps/settings/partials/common.py
# Load values from environment variables

import os
import ast

from .production import *

from django.core.exceptions import ImproperlyConfigured


def get_env_value(env_variable, default=None):
    """Get the environment variable value or return its default value."""
    try:
        return os.environ[env_variable]
    except KeyError:
        if isinstance(default, str):
            return default
        else:
            error_msg = 'Set the {} environment variable'.format(env_variable)
            raise ImproperlyConfigured(error_msg)


def get_env_value_as_dict(env_variable, default=None):
    """Get the environment variable value has a dict or return its default value."""
    try:
        return ast.literal_eval(os.environ[env_variable])
    except KeyError:
        if isinstance(default, dict):
            return default
        else:
            error_msg = 'Set the {} environment variable'.format(env_variable)
            raise ImproperlyConfigured(error_msg)

def get_env_value_as_bool(env_variable, default=None):
    return get_env_value(env_variable, str(default)).lower() in ("yes", "true", "t", "1")    

SECRET_KEY = get_env_value("DISCOVERY_SECRET_KEY")
ALLOWED_HOSTS = [
    "discovery",
    get_env_value("DISCOVERY_HOST")
]

PLATFORM_NAME = get_env_value("PLATFORM_NAME")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": get_env_value("MYSQL_DATABASE"),
        "USER": get_env_value("MYSQL_USERNAME"),
        "PASSWORD": get_env_value("MYSQL_PASSWORD"),
        "HOST": get_env_value("MYSQL_HOST"),
        "PORT": int(get_env_value("MYSQL_PORT")),
        "OPTIONS": {
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    },
    "read_replica": {
        "ENGINE": "django.db.backends.",
        "HOST": get_env_value("MYSQL_READ_REPLICA_HOST"),
        "PORT": int(get_env_value("MYSQL_READ_REPLICA_PORT", default=get_env_value("MYSQL_PORT"))),
        "NAME": get_env_value("MYSQL_READ_REPLICA_DATABASE", default=get_env_value("MYSQL_DATABASE")),
        "USER": get_env_value("MYSQL_READ_REPLICA_USERNAME"),
        "PASSWORD": get_env_value("MYSQL_READ_REPLICA_PASSWORD"),
        "ATOMIC_REQUESTS": False,
    },
}

ELASTICSEARCH_DSL['default'].update({ 'hosts': get_env_value("ELASTICSEARCH_HOST_PORT") })

for name, index in get_env_value_as_dict('DISCOVERY_INDEX_OVERRIDES', default={}).items():
    ELASTICSEARCH_INDEX_NAMES[name] = index

CACHES = {
    "default": {
        "BACKEND": get_env_value("CACHE_BACKEND", default="django_redis.cache.RedisCache"),
        "KEY_PREFIX": get_env_value("CACHE_KEY_PREFIX", default="discovery"),
        "LOCATION": get_env_value("CACHE_LOCATION"),
    }
}

# Some openedx language codes are not standard, such as zh-cn
LANGUAGE_CODE = {
    "zh-cn": "zh-hans",
    "zh-hk": "zh-hant",
    "zh-tw": "zh-hant",
}.get(get_env_value("LANGUAGE_CODE"), get_env_value("LANGUAGE_CODE"))
PARLER_DEFAULT_LANGUAGE_CODE = LANGUAGE_CODE
PARLER_LANGUAGES[1][0]["code"] = LANGUAGE_CODE
PARLER_LANGUAGES["default"]["fallbacks"] = [PARLER_DEFAULT_LANGUAGE_CODE]

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = get_env_value("SMTP_HOST")
EMAIL_PORT = int(get_env_value("SMTP_PORT", default=(587 if get_env_value_as_bool("SMTP_USE_TLS", False) else 25)))
EMAIL_HOST_USER = get_env_value("SMTP_USERNAME", default="")
EMAIL_HOST_PASSWORD = get_env_value("SMTP_PASSWORD", default="")
EMAIL_USE_TLS = get_env_value_as_bool("SMTP_USE_TLS", default=False)

# Get rid of the "local" handler
LOGGING["handlers"].pop("local", None)
for logger in LOGGING["loggers"].values():
    if "local" in logger["handlers"]:
        logger["handlers"].remove("local")
# Decrease verbosity of algolia logger
LOGGING["loggers"]["algoliasearch_django"] = {"level": "WARNING"}

OAUTH_API_TIMEOUT = 5

import json
JWT_AUTH["JWT_ISSUER"] = get_env_value("JWT_COMMON_ISSUER")
JWT_AUTH["JWT_AUDIENCE"] = get_env_value("JWT_COMMON_AUDIENCE")
JWT_AUTH["JWT_SECRET_KEY"] = get_env_value("JWT_COMMON_SECRET_KEY")
JWT_AUTH["JWT_PUBLIC_SIGNING_JWK_SET"] = json.dumps(get_env_value("JWT_PUBLIC_SIGNING_JWK_SET"))
JWT_AUTH["JWT_ISSUERS"] = [
    {
        "ISSUER": get_env_value("JWT_COMMON_ISSUER"),
        "AUDIENCE": get_env_value("JWT_COMMON_AUDIENCE"),
        "SECRET_KEY": get_env_value("OPENEDX_SECRET_KEY"),
    }
]

EDX_DRF_EXTENSIONS = {
    'OAUTH2_USER_INFO_URL': get_env_value("OAUTH2_USER_INFO_URL", default=get_env_value("LMS_BASE_URL") + "/oauth2/user_info"),
}



BACKEND_SERVICE_EDX_OAUTH2_KEY = get_env_value("BACKEND_SERVICE_EDX_OAUTH2_KEY")
BACKEND_SERVICE_EDX_OAUTH2_SECRET = get_env_value("BACKEND_SERVICE_EDX_OAUTH2_SECRET")
BACKEND_SERVICE_EDX_OAUTH2_PROVIDER_URL = get_env_value("BACKEND_SERVICE_EDX_OAUTH2_PROVIDER_URL", default="http://lms:8000/oauth2")

SOCIAL_AUTH_EDX_OAUTH2_KEY = get_env_value("SOCIAL_AUTH_EDX_OAUTH2_KEY")
SOCIAL_AUTH_EDX_OAUTH2_SECRET = get_env_value("SOCIAL_AUTH_EDX_OAUTH2_SECRET")
SOCIAL_AUTH_EDX_OAUTH2_ISSUER = get_env_value("SOCIAL_AUTH_EDX_OAUTH2_ISSUER", default=get_env_value("LMS_BASE_URL"))
SOCIAL_AUTH_EDX_OAUTH2_URL_ROOT = SOCIAL_AUTH_EDX_OAUTH2_ISSUER
SOCIAL_AUTH_EDX_OAUTH2_PUBLIC_URL_ROOT = SOCIAL_AUTH_EDX_OAUTH2_ISSUER
SOCIAL_AUTH_EDX_OAUTH2_LOGOUT_URL = SOCIAL_AUTH_EDX_OAUTH2_ISSUER + "/logout"

SOCIAL_AUTH_REDIRECT_IS_HTTPS = get_env_value_as_bool("SOCIAL_AUTH_REDIRECT_IS_HTTPS", default=True)
