"""
Specific overrides to the base, lms and cms, production settings to NAU.
"""
import sys

# By default load the production settings and not the tutor ones.
from .production import *

# Nevertheless we still prefer to use the tutor configuration for logging.
# It removes the syslog base logger.
#
# Adapted from tutor:
#   https://github.com/overhangio/tutor/blob/v12.2.0/tutor/templates/apps/openedx/settings/partials/common_all.py#L85-L97
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


# Language/locales
# Tutor builds docker image with an extra locale path and translations from github.com/openedx/openedx-i18n repository.
# https://github.com/overhangio/tutor/blob/b4f905c2aab1bb7ee7adbb25cff659bb029e7eb5/tutor/templates/build/openedx/Dockerfile#L62
LOCALE_PATHS.append("/openedx/locale/contrib/locale")
LOCALE_PATHS.append("/openedx/locale/user/locale")


# When we disable this feature, `FEATURES['ENABLE_CSMH_EXTENDED']`, 
# we need to remove the next installed app and its database router.
# If we disable it, we are not using the `csmh` database.
#
# Reference:
#   https://github.com/openedx/edx-platform/blob/9d349a8ecd95443fa22fd3503978e66e5d770e10/lms/envs/common.py#L732-L735
# 
# Code adapted from:
#   https://github.com/overhangio/tutor/blob/3f1dd832e49f58a664e62a633ae94c0339727b10/tutor/templates/apps/openedx/settings/partials/common_all.py#L59-L64
# 
if not FEATURES['ENABLE_CSMH_EXTENDED']:
    # Get rid completely of coursewarehistoryextended, as we do not use the CSMH database
    INSTALLED_APPS.remove("lms.djangoapps.coursewarehistoryextended")
    DATABASE_ROUTERS.remove(
        "openedx.core.lib.django_courseware_routers.StudentModuleHistoryExtendedRouter"
    )

# Sentry
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
SENTRY_DSN = ENV_TOKENS.get('SENTRY_DSN', SENTRY_DSN)
SENTRY_ENVIRONMENT = ENV_TOKENS.get('SENTRY_ENVIRONMENT', SENTRY_ENVIRONMENT)
SENTRY_ENABLE_TRACKING = ENV_TOKENS.get('SENTRY_ENABLE_TRACKING', SENTRY_ENABLE_TRACKING)
sentry_sdk.init(
    dsn=SENTRY_DSN,
    integrations=[DjangoIntegration()],
    environment=SENTRY_ENVIRONMENT,
    enable_tracing=SENTRY_ENABLE_TRACKING,
)
