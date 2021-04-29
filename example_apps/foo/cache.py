from django_cache.contrib import (
    CacheWorker, automatic_invalidation,
    workers_collection,
    default_outdated_getter,
    default_newcomers_getter
)
from django_cache.shortcuts import get_cache_worker
from .getters import get_foo, get_bar, get_foo_with_nested

from .models import Foo, Bar


simple_foo = CacheWorker(
    structure_getter=get_foo,
    label='simple_foo',
    timeout=20,
)
workers_collection.register(
    structure_getter=get_bar,
    label="simple_bar",
    timeout=20,
)
simple_bar = get_cache_worker("simple_bar")

fast_foo_cache = CacheWorker(
    structure_getter=get_foo,
    label="fast_foo_cache",
    timeout=10,
    relevance_timeout=1,
    relevance_invalidation=True
)
fast_foo_timeout_cache = CacheWorker(
    structure_getter=get_foo,
    label="fast_foo_cache",
    timeout=10,
    relevance_invalidation=True,
    relevance_timeout=1,
)
nested_foo_cache = CacheWorker(
    structure_getter=get_foo_with_nested,
    label="nested_foo_cache",
    timeout=10,
)


automatic_invalidation.register(
    Bar, {
        "simple_bar": {
            "instance_getter": lambda instance: {
                "attr1": instance.attr1, "attr2": instance.attr2, "attr3": instance.attr3
            },
        },
        "nested_foo_cache": {
            "instance_getter": lambda instance: {"bars": instance.id},
            "outdated_getter": default_outdated_getter(["bars", "id"]),
            "newcomers_getter": default_newcomers_getter(["bars", "id"])
        }
    }
)
automatic_invalidation.register(
    Foo, {
        "all_foos": {"is_empty": True}
    }
)
