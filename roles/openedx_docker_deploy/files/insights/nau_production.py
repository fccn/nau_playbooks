from .production import *

# Get rid of the "local" handler
LOGGING["handlers"].pop("local")
for logger in LOGGING["loggers"].values():
    if "local" in logger["handlers"]:
        logger["handlers"].remove("local")
