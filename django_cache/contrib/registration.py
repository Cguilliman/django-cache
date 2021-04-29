from typing import *
from django.conf import settings
from django.utils.module_loading import import_string

from .cache import CacheWorker
from . import settings as default
from .settings import DEFAULT_KEYGEN, DEFAULT_TICK_AMOUNT, DEFAULT_TICK_SIZE, DEFAULT_TIMEOUT


_CREATION_FIELDS = (
    "structure_getter", "label", "timeout",
    "key_gen", "tick_amount", "tick",
)


class WorkersCollection:
    workers = {}

    def __init__(self, workers_settings: List):
        for worker in workers_settings:
            self.register(**{key: worker.get(key) for key in _CREATION_FIELDS})

    def register(
        self,
        structure_getter: Union[str, Callable[..., Any]],
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
        self.register_worker(label, CacheWorker(
            structure_getter=structure_getter,
            label=label,
            timeout=timeout,
            key_gen=key_gen,
            cached_entity=cached_entity,
            tick_amount=tick_amount,
            tick=tick,
            delay_invalidation=delay_invalidation,
            relevance_invalidation=relevance_invalidation,
            relevance_timeout=relevance_timeout,
            delay_countdown=delay_countdown,
            delay_logging=delay_logging,
        ))

    def register_worker(self, label: str, worker: CacheWorker):
        self.workers[label] = worker

    def get(self, label: str) -> Optional[CacheWorker]:
        return self.workers.get(label)


workers_collection = WorkersCollection(
    getattr(settings, "DJANGO_CACHE_WORKERS", [])
)
