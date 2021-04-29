from django_cache.contrib import CacheWorker, automatic_invalidation
from django_cache.contrib import workers_collection
from django_cache.shortcuts import get_cache_worker

from .models import Foo, Bar


def get_foo(attr1, attr2, attr3):
    return Foo.objects.filter(attr1=attr1, attr2=attr2, attr3=attr3)


def get_bar(**kwargs):
    return Bar.objects.filter(**kwargs)


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


automatic_invalidation.register(
    Bar, {
        "simple_bar": {
            "instance_getter": lambda instance: {
                "attr1": instance.attr1, "attr2": instance.attr2, "attr3": instance.attr3
            },
        }
    }
)
