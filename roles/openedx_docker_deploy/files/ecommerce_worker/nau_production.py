# Adapted from tutor-ecommerce https://github.com/overhangio/tutor-discovery
# Load values from environment variables

import logging.config
import yaml
from ecommerce_worker.configuration import get_overrides_filename
from ecommerce_worker.configuration.base import *
from ecommerce_worker.configuration.logger import get_logger_config

# For the record, we can't import settings from production module because a syslogger is
# configured there.

# BROKER_URL = "redis://{% if REDIS_USERNAME and REDIS_PASSWORD %}{{ REDIS_USERNAME }}:{{ REDIS_PASSWORD }}@{% endif %}{{ REDIS_HOST }}:{{ REDIS_PORT }}"

JWT_SECRET_KEY = "{{ JWT_COMMON_SECRET_KEY }}"
JWT_ISSUER = "{{ JWT_COMMON_ISSUER }}"

# Logging: get rid of local handler
logging_config = get_logger_config(
    log_dir="/var/log",
    edx_filename="ecommerce_worker.log",
    dev_env=True,
    debug=False,
    local_loglevel="INFO",
)
logging_config["handlers"].pop("local")
for logger in logging_config["loggers"].values():
    try:
        logger["handlers"].remove("local")
    except ValueError:
        continue
logging.config.dictConfig(logging_config)


# Load settings from yaml file
filename = get_overrides_filename('ECOMMERCE_WORKER_CFG')
with open(filename) as f:
    config_from_yaml = yaml.safe_load(f)

# Override base configuration with values from disk.
vars().update(config_from_yaml)
