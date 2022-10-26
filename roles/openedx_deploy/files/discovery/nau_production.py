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


# Get rid of the "local" handler
LOGGING["handlers"].pop("local", None)
for logger in LOGGING["loggers"].values():
    if "local" in logger["handlers"]:
        logger["handlers"].remove("local")
# Decrease verbosity of algolia logger
LOGGING["loggers"]["algoliasearch_django"] = {"level": "WARNING"}

# Overwrite elasticsearch configuration that allow to increase the default 10 seconds timeout.
ELASTICSEARCH_TIMEOUT=int(get_env_value("ELASTICSEARCH_TIMEOUT", default=10))
ELASTICSEARCH_DSL['default'].update({
    'hosts': ELASTICSEARCH_CLUSTER_URL,
    'timeout': ELASTICSEARCH_TIMEOUT,
})
