"""
WSGI config for LMS.

This module contains the WSGI application used by Django's development server
and any production WSGI deployments.
It exposes a module-level variable named ``application``. Django's
``runserver`` and ``runfcgi`` commands discover this application via the
``WSGI_APPLICATION`` setting.

NAU custom:  it starts the module store and close all caches only after the post fork
of the uwsgi worker.
"""

# Patch the xml libs
from safe_lxml import defuse_xml_libs
defuse_xml_libs()

import os  # lint-amnesty, pylint: disable=wrong-import-order, wrong-import-position
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lms.envs.aws")

import lms.startup as startup  # lint-amnesty, pylint: disable=wrong-import-position
startup.run()

from xmodule.modulestore.django import modulestore  # lint-amnesty, pylint: disable=wrong-import-position


def close_all_caches():
    """
    Close the cache so that newly forked workers cannot accidentally share
    the socket with the processes they were forked from. This prevents a race
    condition in which one worker could get a cache response intended for
    another worker.
    We do this in a way that is safe for 1.4 and 1.8 while we still have some
    1.4 installations.
    """
    from django.conf import settings
    from django.core import cache as django_cache
    if hasattr(django_cache, 'caches'):
        get_cache = django_cache.caches.__getitem__
    else:
        get_cache = django_cache.get_cache  # pylint: disable=no-member
    for cache_name in settings.CACHES:
        cache = get_cache(cache_name)
        if hasattr(cache, 'close'):
            cache.close()

    # The 1.4 global default cache object needs to be closed also: 1.4
    # doesn't ensure you get the same object when requesting the same
    # cache. The global default is a separate Python object from the cache
    # you get with get_cache("default"), so it will have its own connection
    # that needs to be closed.
    cache = django_cache.cache
    if hasattr(cache, 'close'):
        cache.close()

import uwsgidecorators  # lint-amnesty, pylint: disable=wrong-import-order, wrong-import-position

@uwsgidecorators.postfork
def post_fork():
    # Trigger a forced initialization of our modulestores since this can take a
    # while to complete and we want this done before HTTP requests are accepted.
    modulestore()
    close_all_caches()

# This application object is used by the development server
# as well as any WSGI server configured to use this file.
from django.core.wsgi import get_wsgi_application  # lint-amnesty, pylint: disable=wrong-import-order, wrong-import-position
application = get_wsgi_application()
