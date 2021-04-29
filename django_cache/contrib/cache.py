from typing import Callable, Union, Any, Generator
import time
from datetime import datetime, timedelta

from django.core.cache import cache

from .save import cache_value, CachedEntity
from . import settings as default


def get_precache_key(key):
    return f"{key}||PRECACHE"


class CacheWorker:

    def __init__(
        self,
        structure_getter: Callable[..., Any],
        label: str,
        timeout: int = default.DEFAULT_TIMEOUT,
        key_gen: Union[str, Callable[..., str]] = default.DEFAULT_KEYGEN,
        cached_entity: bool = False,
        tick_amount: int = default.DEFAULT_TICK_AMOUNT,
        tick: float = default.DEFAULT_TICK_SIZE,
        delay_invalidation: bool = default.DEFAULT_DELAY_INVALIDATION,
        relevance_invalidation: bool = default.DEFAULT_RELEVANCE_INVALIDATION,
        relevance_timeout: int = default.DEFAULT_RELEVANCE_TIMEOUT,
        delay_countdown: int = default.DEFAULT_DELAY_COUNTDOWN,
        delay_logging: bool = default.DEFAULT_DELAY_LOGGING,
        is_register: bool = True
    ):
        # General
        self.label = label
        self.key_gen = key_gen
        self.structure_getter = structure_getter
        self.timeout = timeout
        self.cached_entity = cached_entity
        # Ticks configure
        self.tick_amount = tick_amount
        self.tick = tick
        # Logging
        self.delay_logging = delay_logging
        # Invalidation by timeout
        self.relevance_invalidation = relevance_invalidation
        self.relevance_timeout = relevance_timeout
        self.delay_invalidation = delay_invalidation
        self.delay_countdown = delay_countdown
        if is_register:
            self.__register()

    def __register(self):
        from .registration import workers_collection
        workers_collection.register_worker(self.label, self)

    def get_key(self, *args, **kwargs):
        return f"{self.label}@{self.key_gen(*args, **kwargs)}"

    def save(self, *args, **kwargs):
        key = self.get_key(*args, **kwargs)
        # Save precache
        cache.set(get_precache_key(key), True, 10)
        return self.base_save(key_=key, *args, **kwargs)

    def base_save(self, key_=None, *args, **kwargs):
        if not key_:
            key_ = self.get_key(*args, **kwargs)
        entity = CachedEntity(
            value=self.structure_getter(*args, **kwargs),
            key=key_,
            label=self.label,
            timeout=self.timeout,
            is_relevance_invalidation=self.relevance_invalidation,
            created_at=datetime.now(),
            available_to=datetime.now() + timedelta(seconds=self.timeout),
            relevance_to=datetime.now() + timedelta(seconds=self.relevance_timeout)
        )
        cache_value(
            cache_entity=entity,
            is_delay=self.delay_logging,
            *args, **kwargs
        )
        return entity if self.cached_entity else entity.value

    def _get(self, key):
        value_data = cache.get(key)
        if not value_data:
            return
        entity = CachedEntity(**value_data)
        # Check by relevance and do invalidation if need it
        if self.relevance_invalidation and entity.relevance_to <= datetime.now():
            from ..tasks import lazy_invalidation_task
            if not self.delay_invalidation:
                return lazy_invalidation_task(key)
            # Will run invalidation in delay, and return old cached value
            lazy_invalidation_task.delay(key)

        return entity if self.cached_entity else entity.value

    def cache_ticks_getter(self, key) -> Generator:
        # Try to get cache
        yield self._get(key)
        # Get precached marker
        is_precached = cache.get(get_precache_key(key))
        if not is_precached:
            return
        for _ in range(self.tick_amount):
            time.sleep(self.tick)
            yield self._get(key)

    def get(self, *args, **kwargs):
        for cached_data in self.cache_ticks_getter(self.get_key(*args, **kwargs)):
            if cached_data:
                return cached_data
        return self.save(*args, **kwargs)

    def clear_all(self):
        cache.delete_pattern(f"{self.label}*")
