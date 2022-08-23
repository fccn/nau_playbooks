"""
Specific overrides to the base prod settings to NAU.
"""
import sys

from .production import *

# Adapted from tutor
# https://github.com/overhangio/tutor/blob/v12.2.0/tutor/templates/apps/openedx/settings/partials/common_all.py#L85-L97

# Change syslog-based loggers which don't work inside docker containers
LOGGING["handlers"]["local"] = {
    "class": "logging.StreamHandler",
    "stream": sys.stdout,
    "formatter": "standard",
}
LOGGING["handlers"]["tracking"] = {
    "level": "DEBUG",
    "class": "logging.StreamHandler",
    "stream": sys.stdout,
    "formatter": "raw",
}
LOGGING["loggers"]["tracking"]["handlers"] = ["console", "local", "tracking"]
# Silence some loggers (note: we must attempt to get rid of these when upgrading from one release to the next)
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="newrelic.console")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="lms.djangoapps.course_wiki.plugins.markdownedx.wiki_plugin")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="wiki.plugins.links.wiki_plugin")
