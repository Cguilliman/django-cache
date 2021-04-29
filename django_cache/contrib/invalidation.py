import itertools
from functools import reduce
from operator import and_, or_
from typing import Iterable, Dict, Any, List, Iterator

from django.utils.timezone import datetime
from django.db.models import Q

from ..models import CreatedCache
from .registration import workers_collection
from .cache import CacheWorker


def get_attributes_from_object(cache_object: CreatedCache):
    return (
        cache_object.attributes.get("args"),
        cache_object.attributes.get("kwargs")
    )


def invalidate_created_caches(
    cache_object: CreatedCache,
    cache_worker: CacheWorker,
    *,
    is_delete: bool = True
):
    args, kwargs = get_attributes_from_object(cache_object)
    cache_worker.base_save(*args, **kwargs)
    if is_delete:
        cache_object.delete()


def get_group_variations_getter(names: Iterable[str]):
    sorted_names = sorted(names)

    def getter(filters: Dict[str, Any]) -> List[Any]:
        # Build all available values groups
        return list(itertools.product(*(filters[name] for name in sorted_names)))
    return getter, sorted_names


def get_differance_attributes(outdated: Dict, newcomers: Dict) -> [Iterable[Iterable[Any]], List[str]]:
    instance_attributes = {}
    newcomers_attributes = {}
    for key, value in newcomers.items():
        old_value = outdated.get(key)
        if value != old_value:
            instance_attributes[key] = [old_value, None]
            newcomers_attributes[key] = [value, None]
    get_groups, names = get_group_variations_getter(instance_attributes.keys())
    return itertools.chain(get_groups(instance_attributes), get_groups(newcomers_attributes)), names


def get_instance_attributes(instance: Dict) -> [Iterable[Iterable[Any]], List[str]]:
    instance_attributes = {key: [value, None] for key, value in instance.items()}
    get_groups, names = get_group_variations_getter(instance_attributes)
    return get_groups(instance_attributes), names


def build_attributes_filter_groups(outdated: Dict, newcomers: Dict = None) -> Iterator[Q]:
    attributes, names = (
        get_differance_attributes(outdated, newcomers)
        if newcomers else get_instance_attributes(outdated)
    )
    for attributes_group in attributes:
        yield (reduce(and_, [
            (
                Q(**{f"attributes__filterable_kwargs__{attribute}__isnull": True})
                if value is None
                else Q(**{f"attributes__filterable_kwargs__{attribute}__contains": value}))
            for attribute, value in zip(names, attributes_group)
        ]))


def get_created_cache(label, outdated: Dict = None, newcomers: Dict = None):
    if outdated:
        attributes_filters = reduce(or_, [Q(item) for item in build_attributes_filter_groups(outdated, newcomers)])
        return CreatedCache.objects.filter(Q(label=label) & Q(attributes_filters))
    return CreatedCache.objects.filter(label=label)


def invalidate_process(cache_worker: CacheWorker, outdated: Dict = None, newcomers: Dict = None):
    for cached_object in get_created_cache(cache_worker.label, outdated, newcomers):
        invalidate_created_caches(cached_object, cache_worker)


def invalidate_all_process(cache_worker):
    for cached_object in CreatedCache.objects.filter(label=cache_worker.label):
        invalidate_created_caches(cached_object, cache_worker)


def invalidate_by_relevance_timeout():
    to_invalidation = CreatedCache.objects.filter(
        is_relevance_invalidation=True,
        relevance_to__lte=datetime.now()
    )
    for cached_object in to_invalidation:
        cache_worker = workers_collection.get(cached_object.label)
        invalidate_created_caches(cached_object, cache_worker)


def lazy_invalidation(key: str):
    cached_object = CreatedCache.objects.filter(key=key).first()
    cache_worker = workers_collection.get(cached_object.label)
    invalidate_created_caches(cached_object, cache_worker)


INVALIDATE = "i"
INVALIDATE_ALL = "ia"
INVALIDATION_PROCESSES = {
    INVALIDATE: invalidate_process,
    INVALIDATE_ALL: invalidate_all_process,
}


def get_invalidation_func(invalidation_type):

    def wrapped(cache_worker: CacheWorker, *args, **kwargs):
        is_delay = kwargs.pop("is_delay", False)
        if is_delay or cache_worker.delay_invalidation:
            from ..tasks import run_invalidate_task
            run_invalidate_task.apply_async(
                args=(invalidation_type, cache_worker.label, *args),
                kwargs=kwargs,
                countdown=cache_worker.delay_countdown
            )
        else:
            INVALIDATION_PROCESSES.get(invalidation_type)(cache_worker, *args, **kwargs)
    return wrapped


invalidate_all = get_invalidation_func(INVALIDATE_ALL)
invalidate = get_invalidation_func(INVALIDATE)
