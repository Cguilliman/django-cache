from typing import Dict, Any

from .contrib import workers_collection, CacheWorker, invalidate, invalidate_all


def get_cache_worker(label: str) -> CacheWorker:
    return workers_collection.get(label)


def get_cache(label: str, *args, **kwargs) -> Any:
    return get_cache_worker(label).get(*args, **kwargs)


def save_cache(label: str, *args, **kwargs) -> Any:
    return get_cache_worker(label).save(*args, **kwargs)


def clear_all(label: str):
    get_cache_worker(label).clear_all()


def invalidate_cache(label: str, old_data: Dict, new_data: Dict = None):
    worker = get_cache_worker(label)
    invalidate(worker, old_data, new_data)


def invalidate_all_cache(label: str):
    worker = get_cache_worker(label)
    invalidate_all(worker)
