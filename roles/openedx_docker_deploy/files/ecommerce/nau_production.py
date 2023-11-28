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
