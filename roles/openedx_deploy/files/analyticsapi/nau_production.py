"""
Specific overrides to the production.py settings for the analytics api open edx project.
"""
import sys

from .production import *

# Change local logging handler.
# It removes the syslog base logger.
#
# Change syslog-based loggers which don't work inside docker containers
LOGGING["handlers"]["local"] = {
    "class": "logging.StreamHandler",
    "stream": sys.stdout,
    "formatter": "standard",
}
