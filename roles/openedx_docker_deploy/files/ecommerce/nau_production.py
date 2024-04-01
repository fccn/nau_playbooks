# Adapted from tutor-ecommerce https://github.com/overhangio/tutor-ecommerce
from .production import *

# Allow to overwrite the LOCALE_PATHS from the ECOMMERCE_CFG yaml file.
# But because it's converted to a list instead of a tuple, we need to convert
# it to a tuple.
LOCALE_PATHS = tuple(LOCALE_PATHS)

# Additional installed apps
for app in config_from_yaml.get('ADDL_INSTALLED_APPS', []):
    INSTALLED_APPS.append(app)

PAYMENT_PROCESSORS = list(PAYMENT_PROCESSORS) + EXTRA_PAYMENT_PROCESSOR_CLASSES
EXTRA_PAYMENT_PROCESSOR_URLS = config_from_yaml.get('EXTRA_PAYMENT_PROCESSOR_URLS', {})

# Get rid of the "local" handler
LOGGING["handlers"].pop("local", None)
for logger in LOGGING["loggers"].values():
    if "local" in logger["handlers"]:
        logger["handlers"].remove("local")
# Decrease verbosity of algolia logger
LOGGING["loggers"]["algoliasearch_django"] = {"level": "WARNING"}

# Sentry
import sentry_sdk
from os import environ
from sentry_sdk.integrations.django import DjangoIntegration
SENTRY_DSN = environ.get('SENTRY_DSN', config_from_yaml.get('SENTRY_DSN', None))
SENTRY_ENVIRONMENT = environ.get('SENTRY_ENVIRONMENT', config_from_yaml.get('SENTRY_ENVIRONMENT', None))
SENTRY_TRACES_SAMPLE_RATE = environ.get('SENTRY_TRACES_SAMPLE_RATE', config_from_yaml.get('SENTRY_TRACES_SAMPLE_RATE', None))
sentry_sdk.init(
    dsn=SENTRY_DSN,
    integrations=[DjangoIntegration()],
    environment=SENTRY_ENVIRONMENT,
    traces_sample_rate=SENTRY_TRACES_SAMPLE_RATE,
)
