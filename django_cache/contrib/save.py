from typing import NamedTuple, Any
from datetime import datetime

from django.core.cache import cache

from django_cache.models import CreatedCache


# @dataclass
class CachedEntity(NamedTuple):
    label: str
    key: str
    timeout: int
    is_relevance_invalidation: bool
    created_at: datetime
    relevance_to: datetime
    available_to: datetime
    value: Any

    def to_cache(self):
        return {
            "value": self.value,
            "timeout": self.timeout,
            "created_at": self.created_at,
            **self.get_info()
        }

    def get_info(self):
        return {
            "label": self.label,
            "key": self.key,
            "available_to": self.available_to,
            "relevance_to": self.relevance_to,
            "is_relevance_invalidation": self.is_relevance_invalidation,
        }


def serialize_attributes(*args, **kwargs):
    # NOTE: Contain list type in kwargs values
    return {
        "args": args,
        "kwargs": kwargs,
        # TODO: Add types validation
        "filterable_kwargs": {
            key: (
                value
                if isinstance(value, (list, tuple))
                else [value]
            )
            for key, value in kwargs.items()
            if value is not None
        }
    }


def log_cache_value(label, key, is_relevance_invalidation, available_to, relevance_to, *args, **kwargs):
    # Delete exists cache logs with current arguments
    CreatedCache.objects.filter(key=key).delete()
    # Create new log
    return CreatedCache.objects.create(
        key=key,
        label=label,
        is_relevance_invalidation=is_relevance_invalidation,
        attributes=serialize_attributes(*args, **kwargs),
        available_to=available_to,
        relevance_to=relevance_to,
    )


def cache_value(cache_entity: CachedEntity, is_delay=False, *args, **kwargs):
    cache.set(cache_entity.key, cache_entity.to_cache(), cache_entity.timeout)
    kwargs.update(cache_entity.get_info())
    if is_delay:
        from ..tasks import create_cache_log_task
        create_cache_log_task.delay(*args, **kwargs)
    else:
        log_cache_value(*args, **kwargs)
