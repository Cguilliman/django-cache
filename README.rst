Django-cache
============

**Django-cache** implement configurable caching mechanics.

Minimal start
-------------

Installation:

.. code:: shell

    $ pip install django-cache

Register application in settings:

.. code:: python

    INSTALLED_APPS = [
        "django_cache",
    ]

Run migrations:

.. code:: shell

    $ python manage.py migrate

Initialize worker:

.. code:: python

    from django_cache.contrib import CacheWorker

    from my_application import get_all_foo_list

    all_foos_cache = CacheWorker(
        label="all_foos",  # Unique cache worker label
        structure_getter=get_all_foo_list,  # Function which generate cache value
        timeout=100000,  # Cache live in seconds
        delay_invalidation=True
    )

or in settings:

.. code:: python

    DJANGO_CACHE_WORKERS = [
        {
            "label": "all_foos",
            "structure_getter": "my_application.get_all_foo_list",
            "timeout": 100000,
            "delay_invalidation": True,
        }
    ]

Use caching value in your code:

.. code:: python

    from django_cache.shortcuts import get_cache

    def get_foos(requests):
        ...
        foos =  get_cache("all_foos")
        ...

Worker parameters
-----------------

* ``structure_getter`` - [Callable[..., Any]] Function or something callable which create cache value, must receive serializable arguments, which can be converted in string presentation.
* ``label`` - [str] Unique caching worker label.
* ``timeout`` - [int] Cache key live time.
* ``key_gen`` - [Not required] Function which generate key by getting arguments.
* ``cached_entity`` - [Not required][bool] Default False. Will return CacheEntity as cache value.
* ``tick_amount`` - [Not required][int] Default 10. Count of ticks while concurrent getting cache value.
* ``tick`` - [Not required][float/int] Default 0,1. Tick size in seconds.
* ``relevance_invalidation`` - [Not required][bool] Default False. Enable invalidation by relevance.
* ``relevance_timeout`` - [Not required][int] Default 60. Cache value relevance time in seconds.
* ``delay_logging`` - [Not required][bool] Default False. Run CreatedCache object creation in delay celery task.

Automatic invalidation
----------------------

For automatic invalidation you must initialize invalidation arguments getters.

Change your model:

.. code:: python

    from django.db import models

    from model_subscription.models import SubscriptionModelMixin, SubscriptionQuerySet


    class Foo(SubscriptionModelMixin, models.Model):
        attr1 = models.IntegerField()
        attr2 = models.CharField(max_length=255)
        attr3 = models.FloatField(null=True, blank=True)

        objects = SubscriptionQuerySet.as_manager()

Configure invalidation:

.. code:: python

    from django_cache.contrib import Cacher, automatic
    from django_cache.contrib.automatic import (
        default_outdated_getter, default_newcomers_getter
    )

    from my_application.models import Foo


    # Getter without arguments
    def get_all_foo_list():
        return Foo.objects.all()


    all_foos_cache = Cacher(
        label="all_foos",  # Unique cache worker label
        structure_getter=get_all_foo_list,  # Function which generation cache value
        timeout=100000,  # Cache live in seconds
        delay_invalidation=True
    )


    # Filtering by arguments
    def filter_foos(attr1, attr2, **kwargs):
        return Foo.objects.filter(attr1=attr1, attr2=attr2)


    filtered_foos = Cacher(
        label="filtered_foos",  # Unique cache worker label
        structure_getter=filter_foos,  # Function which generation cache value
        timeout=100000,  # Cache live in seconds
        delay_invalidation=True
    )


    def filtered_foos_outdated_getter(instance: Foo, attrs: Dict) -> Dict:
        default_attrs = default_outdated_getter()
        return {
            "attr1": default_attrs.get("attr1"),
            "attr2": default_attrs.get("attr2"),
        }


    def filtered_foos_newcomers_getter(instance: Foo, attrs: Dict) -> Dict:
        default_attrs = default_newcomers_getter()
        return {
            "attr1": default_attrs.get("attr1"),
            "attr2": default_attrs.get("attr2"),
        }


    automatic.register = automatic.register(
        Foo, {
            "all_foos": {"is_empty": True},
            "filtered_foos": {
                # Callable or string (path to callable)
                "instance_getter": lambda instance: {
                    "attr1": instance.attr1, "attr2": instance.attr2
                },
                # Callable or string (path to callable)
                "outdated_getter": filtered_foos_outdated_getter,
                "newcomers_getter": filtered_foos_newcomers_getter,
            }
        }
    )

NOTES
-----

* If you are using delay invalidation with celery, be careful with cache backend. Memcache has two different instances in celery and django, so using redis or rabbitmq backends.

* If you initialize cache worker using ``django_cache.contrib.Cacher``, this module must me received by application.
