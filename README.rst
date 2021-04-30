Django-cache
============

|PyPI version| |python version| |license| |Code Health| |Coverage| |Project Status| |downloads|

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
        expires=100000,  # Cache live in seconds
        delay_invalidation=True
    )

or in settings:

.. code:: python

    DJANGO_CACHE_WORKERS = {
        "all_foos": {
            "label": "",
            "structure_getter": "my_application.get_all_foo_list",
            "expires": 100000,
            "delay_invalidation": True,
        }
    }

**NOTE**: Be careful with circle import while using settings declaration.

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
* ``expires`` - [int] Cache key live time.
* ``key_gen`` - [Not required] Function which generate key by getting arguments.
* ``cached_entity`` - [Not required][bool] Default False. Will return CacheEntity as cache value.
* ``tick_amount`` - [Not required][int] Default 10. Count of ticks while concurrent getting cache value.
* ``tick`` - [Not required][float/int] Default 0,1. Tick size in seconds.
* ``relevance_invalidation`` - [Not required][bool] Default False. Enable invalidation by relevance.
* ``relevance_expires`` - [Not required][int] Default 60. Cache value relevance time in seconds.
* ``delay_logging`` - [Not required][bool] Default False. Run CreatedCache object creation in delay celery task.
* ``is_concurrent`` - [Not required][bool] Default True. Enable concurrent cache getting mechanic.

You can change global default value in settings:

* ``DJANGO_CACHE_DEFAULT_TICK_AMOUNT``
* ``DJANGO_CACHE_DEFAULT_TICK_SIZE``
* ``DJANGO_CACHE_DEFAULT_KEYGEN``
* ``DJANGO_CACHE_DEFAULT_EXPIRES``
* ``DJANGO_CACHE_DEFAULT_DELAY_INVALIDATION``
* ``DJANGO_CACHE_DEFAULT_RELEVANCE_INVALIDATION``
* ``DJANGO_CACHE_DEFAULT_RELEVANCE_EXPIRES``
* ``DJANGO_CACHE_DEFAULT_DELAY_COUNTDOWN``
* ``DJANGO_CACHE_DEFAULT_DELAY_LOGGING``
* ``DJANGO_CACHE_IS_CONCURRENT``

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

    from django_cache.contrib import CacheWorker, automatic
    from django_cache.contrib.automatic import (
        default_outdated_getter, default_newcomers_getter
    )

    from my_application.models import Foo


    # Getter without arguments
    def get_all_foo_list():
        return Foo.objects.all()


    all_foos_cache = CacheWorker(
        label="all_foos",  # Unique cache worker label
        structure_getter=get_all_foo_list,  # Function which generation cache value
        expires=100000,  # Cache live in seconds
        delay_invalidation=True
    )


    # Filtering by arguments
    def filter_foos(attr1, attr2, **kwargs):
        return Foo.objects.filter(attr1=attr1, attr2=attr2)


    filtered_foos = CacheWorker(
        label="filtered_foos",  # Unique cache worker label
        structure_getter=filter_foos,  # Function which generation cache value
        expires=100000,  # Cache live in seconds
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

* If you initialize cache worker using ``django_cache.contrib.CacheWorker``, this module must me received by application.

.. |PyPI version| image:: https://badge.fury.io/py/django-ib-cache.svg
   :target: https://badge.fury.io/py/django-ib-cache
.. |python version| image:: https://img.shields.io/pypi/pyversions/django-ib-cache
   :target: https://pypi.org/project/django-ib-cache
.. |license| image:: https://img.shields.io/pypi/l/django-ib-cache.svg
   :alt: Software license
   :target: https://github.com/Cguilliman/django-cache/blob/master/LICENSE
.. |Code Health| image:: https://app.codacy.com/project/badge/Grade/c407b57a01ed4b4eac16bc91620d403b
   :target: https://www.codacy.com/gh/Cguilliman/django-cache
.. |Coverage| image:: https://app.codacy.com/project/badge/Coverage/c407b57a01ed4b4eac16bc91620d403b
   :target: https://www.codacy.com/gh/Cguilliman/django-cache/dashboard
   :alt: Code coverage
.. |Project Status| image:: https://img.shields.io/pypi/status/django-ib-cache.svg
   :target: https://pypi.org/project/django-ib-cache/
   :alt: Project Status
.. |downloads| image:: https://img.shields.io/pypi/dm/django-ib-cache.svg
   :alt: Project Status
