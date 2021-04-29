from typing import (
    Optional, Callable, Iterable, Union, Tuple, Dict, List, Type
)
from dataclasses import dataclass
from collections import defaultdict
from functools import partial
from enum import IntEnum

from django.utils.module_loading import import_string

from model_subscription.decorators import subscribe
from model_subscription.constants import OperationType

from .registration import workers_collection
from .cache import CacheWorker
from .invalidation import invalidate


def ready_to_invalidation(instance, *args, **kwargs):
    for item in automatic_invalidation.get(instance.__class__):  # type: InvalidationWorker
        if not item.is_invalidate or item.is_invalidate(instance, *args, **kwargs):
            if item.is_empty:
                invalidate(item.worker)
            else:
                yield item


def update_exists(instance):
    for item in ready_to_invalidation(instance):
        invalidate(item.worker, item.instance_getter(instance))


def invalidate_changed(instance, attrs):
    for item in ready_to_invalidation(instance, attrs):
        invalidate(
            item.worker,
            item.outdated_getter(instance, attrs),
            item.newcomers_getter(instance, attrs)
        )


class ChangedAttributesTypes(IntEnum):
    OLD = 0
    NEW = 1


def attribute_getter(
        filterable_attributes: Iterable[Union[str, Tuple]] = None,
        data_type: ChangedAttributesTypes = ChangedAttributesTypes.OLD
):
    if filterable_attributes:
        attributes = dict(
            (
                (attr, attr)
                if isinstance(attr, str)
                else (attr[0], attr[1])
            ) for attr in filterable_attributes
        )
    else:
        attributes = None

    def wrapped(instance, attrs):
        data = {}
        if not attributes:
            return None
        for key, values in attrs.items():
            if key in attributes:
                data[attributes.get(key)] = values[data_type]
        return data
    return wrapped


default_outdated_getter = partial(attribute_getter, data_type=ChangedAttributesTypes.OLD)
default_newcomers_getter = partial(attribute_getter, data_type=ChangedAttributesTypes.NEW)


def subscribe_actions(model):
    subscribe(OperationType.CREATE, model)(update_exists)
    subscribe(OperationType.BULK_CREATE, model)(update_exists)
    subscribe(OperationType.UPDATE, model)(invalidate_changed)
    subscribe(OperationType.BULK_UPDATE, model)(invalidate_changed)
    subscribe(OperationType.DELETE, model)(update_exists)
    subscribe(OperationType.BULK_DELETE, model)(update_exists)


@dataclass
class InvalidationWorker:
    worker: CacheWorker
    is_empty: bool
    instance_getter: Optional[Callable]
    outdated_getter: Optional[Callable]
    newcomers_getter: Optional[Callable]
    is_invalidate: Optional[Callable]


class InvalidationSettingsError(Exception):
    pass


def get_func_or_import_from_string(value: Union[str, Callable], is_empty=False):
    if isinstance(value, str):
        value = import_string(value)
    if (is_empty and value is not None) and not callable(value):
        raise InvalidationSettingsError(
            "{} is invalid. Getters must be callable or string path to callable.".format(value)
        )
    return value


class AutomaticInvalidationPool:
    pool: Dict[Type, List[InvalidationWorker]]

    def __init__(self):
        self.pool = defaultdict(list)

    def register(self, model, invalidation_items: Dict):
        for worker_name, getters in invalidation_items.items():
            if getters.get("is_empty"):
                self.pool[model].append(
                    InvalidationWorker(
                        worker=workers_collection.get(worker_name),
                        is_empty=True,
                        instance_getter=None,
                        outdated_getter=None,
                        newcomers_getter=None,
                        is_invalidate=None
                    )
                )
            else:
                self.pool[model].append(InvalidationWorker(
                    worker=workers_collection.get(worker_name),
                    is_empty=False,
                    instance_getter=get_func_or_import_from_string(
                        getters.get("instance_getter", None), True
                    ),
                    outdated_getter=get_func_or_import_from_string(
                        getters.get("outdated_getter", default_outdated_getter())
                    ),
                    newcomers_getter=get_func_or_import_from_string(
                        getters.get("newcomers_getter", default_newcomers_getter())
                    ),
                    is_invalidate=get_func_or_import_from_string(
                        getters.get("is_invalidate", None), True
                    ),
                ))
        subscribe_actions(model)

    def get(self, model):
        return self.pool.get(model, [])


automatic_invalidation = AutomaticInvalidationPool()
