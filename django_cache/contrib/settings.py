from django.conf import settings

from .keygen import keygen


DEFAULT_TICK_AMOUNT = getattr(settings, "DJANGO_CACHE_DEFAULT_TICK_AMOUNT", 10)
DEFAULT_TICK_SIZE = getattr(settings, "DJANGO_CACHE_DEFAULT_TICK_SIZE", 0.1)
DEFAULT_KEYGEN = getattr(settings, "DJANGO_CACHE_DEFAULT_KEYGEN", keygen)
DEFAULT_TIMEOUT = getattr(settings, "DJANGO_CACHE_DEFAULT_TIMEOUT", None)
DEFAULT_DELAY_INVALIDATION = getattr(settings, "DJANGO_CACHE_DEFAULT_DELAY_INVALIDATION", False)
DEFAULT_RELEVANCE_INVALIDATION = getattr(settings, "DJANGO_CACHE_DEFAULT_RELEVANCE_INVALIDATION", False)
DEFAULT_RELEVANCE_TIMEOUT = getattr(settings, "DJANGO_CACHE_DEFAULT_RELEVANCE_TIMEOUT", 60)
DEFAULT_DELAY_COUNTDOWN = getattr(settings, "DJANGO_CACHE_DEFAULT_DELAY_COUNTDOWN", 5)
DEFAULT_DELAY_LOGGING = getattr(settings, "DJANGO_CACHE_DEFAULT_DELAY_LOGGING", False)
