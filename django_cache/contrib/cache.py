from typing import Callable, Union, Any, Generator, NamedTuple
import time
from datetime import datetime, timedelta
from dataclasses import dataclass

from django.core.cache import cache

from .save import cache_value, CachedEntity
from . import settings as default


def get_precache_key(key):
    return f"{key}||PRECACHE"


class LocalSettingsBundle(NamedTuple):
    expires: int
    tick_amount: int
    tick: int
    is_concurrent: bool
    delay_logging: bool
    relevance_invalidation: bool
    relevance_expires: int
    delay_invalidation: bool
    delay_countdown: int


def get_local_settings(attributes, worker: "CacheWorker"):
    return LocalSettingsBundle(**{
        field: attributes.pop(field, getattr(worker, field, None))
        for field in LocalSettingsBundle._fields
    })


class CacheWorker:

    def __init__(
        self,
        structure_getter: Callable[..., Any],
        label: str,
        expires: int = default.DEFAULT_EXPIRES,
        key_gen: Union[str, Callable[..., str]] = default.DEFAULT_KEYGEN,
        cached_entity: bool = False,
        tick_amount: int = default.DEFAULT_TICK_AMOUNT,
        tick: float = default.DEFAULT_TICK_SIZE,
        delay_invalidation: bool = default.DEFAULT_DELAY_INVALIDATION,
        relevance_invalidation: bool = default.DEFAULT_RELEVANCE_INVALIDATION,
        relevance_expires: int = default.DEFAULT_RELEVANCE_EXPIRES,
        delay_countdown: int = default.DEFAULT_DELAY_COUNTDOWN,
        delay_logging: bool = default.DEFAULT_DELAY_LOGGING,
        is_concurrent: bool = default.IS_CONCURRENT,
        is_register: bool = True
    ):
        # General
        self.label = label
        self.key_gen = key_gen
        self.structure_getter = structure_getter
        self.expires = expires
        self.cached_entity = cached_entity
        # Ticks configure
        self.tick_amount = tick_amount
        self.tick = tick
        # Logging
        self.delay_logging = delay_logging
        # Invalidation by expires time
        self.relevance_invalidation = relevance_invalidation
        self.relevance_expires = relevance_expires
        self.delay_invalidation = delay_invalidation
        self.delay_countdown = delay_countdown
        self.is_concurrent = is_concurrent
        if is_register:
            self.__register()

    def __register(self):
        from .registration import workers_collection
        workers_collection.register_worker(self.label, self)

    def get_key(self, *args, **kwargs):
        return f"{self.label}@{self.key_gen(*args, **kwargs)}"

    def save(self, *args, **kwargs):
        local_settings: LocalSettingsBundle = kwargs.pop(
            "local_settings", get_local_settings(kwargs, self)
        )
        key = self.get_key(*args, **kwargs)
        # Save precache
        cache.set(get_precache_key(key), True, 10)
        return self.__save(local_settings=local_settings, key_=key, *args, **kwargs)

    def __save(self, local_settings: LocalSettingsBundle, key_: str = None, *args, **kwargs):
        if not key_:
            key_ = self.get_key(*args, **kwargs)
        now = datetime.now()
        entity = CachedEntity(
            value=self.structure_getter(*args, **kwargs),
            key=key_,
            label=self.label,
            expires=local_settings.expires,
            is_relevance_invalidation=local_settings.relevance_invalidation,
            created_at=now,
            available_to=now + timedelta(seconds=local_settings.expires),
            relevance_to=now + timedelta(seconds=local_settings.relevance_expires)
        )
        cache_value(
            cache_entity=entity,
            is_delay=local_settings.delay_logging,
            *args, **kwargs
        )
        return entity if self.cached_entity else entity.value

    def __get(self, key, local_settings):
        value_data = cache.get(key)
        if not value_data:
            return
        entity = CachedEntity(**value_data)
        # Check by relevance and do invalidation if need it
        if local_settings.relevance_invalidation and entity.relevance_to <= datetime.now():
            from ..tasks import lazy_invalidation_task
            if not local_settings.delay_invalidation:
                return lazy_invalidation_task(key)
            # Will run invalidation in delay, and return old cached value
            lazy_invalidation_task.delay(key)

        return entity if self.cached_entity else entity.value

    def cache_ticks_getter(self, key, local_settings: LocalSettingsBundle) -> Generator:
        # Try to get cache
        yield self.__get(key, local_settings)
        # Get precached marker
        if local_settings.is_concurrent:
            is_precached = cache.get(get_precache_key(key))
            if not is_precached:
                return
            for _ in range(local_settings.tick_amount):
                time.sleep(local_settings.tick)
                yield self.__get(key, local_settings)

    def get(self, *args, **kwargs):
        local_settings: LocalSettingsBundle = get_local_settings(kwargs, self)
        for cached_data in self.cache_ticks_getter(self.get_key(*args, **kwargs), local_settings):
            if cached_data:
                return cached_data
        return self.save(*args, **kwargs)

    def clear_all(self):
        cache.delete_pattern(f"{self.label}*")
