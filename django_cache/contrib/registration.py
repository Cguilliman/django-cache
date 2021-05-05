from typing import Dict, Union, Callable, Any, Optional
from django.conf import settings
from django.utils.module_loading import import_string

from .cache import CacheWorker
from . import settings as default


_CREATION_FIELDS = (
    "structure_getter", "expires",
    "key_gen", "tick_amount", "tick", "cached_entity",
    "delay_invalidation", "relevance_invalidation",
    "relevance_expires", "delay_countdown", "delay_logging",
    "is_concurrent"
)


class WorkersCollection:
    workers = {}

    def __init__(self, workers_settings: Dict):
        for label, worker in workers_settings.items():
            self.register(label=label, **{
                key: worker.get(key)
                for key in _CREATION_FIELDS
                if worker.get(key) is not None
            })

    def register(
        self,
        structure_getter: Union[str, Callable[..., Any]],
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
    ):
        structure_getter = (
            import_string(structure_getter)
            if isinstance(structure_getter, str)
            else structure_getter
        )
        key_gen = (
            import_string(key_gen)
            if isinstance(key_gen, str)
            else key_gen
        )
        worker = CacheWorker(
            structure_getter=structure_getter,
            label=label,
            expires=expires,
            key_gen=key_gen,
            cached_entity=cached_entity,
            tick_amount=tick_amount,
            tick=tick,
            delay_invalidation=delay_invalidation,
            relevance_invalidation=relevance_invalidation,
            relevance_expires=relevance_expires,
            delay_countdown=delay_countdown,
            delay_logging=delay_logging,
            is_concurrent=is_concurrent,
            # To get around circle import exception
            is_register=False
        )
        self.register_worker(label, worker)

    def register_worker(self, label: str, worker: CacheWorker):
        self.workers[label] = worker

    def get(self, label: str) -> Optional[CacheWorker]:
        return self.workers.get(label)


workers_collection = WorkersCollection(
    getattr(settings, "DJANGO_CACHE_WORKERS", {})
)
