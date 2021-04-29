import time

from django.test import TestCase
from django.core.cache import cache

from django_cache.shortcuts import (
    get_cache_worker, get_cache, save_cache,
    invalidate_cache, invalidate_all_cache
)
from django_cache.contrib.invalidation import invalidate, INVALIDATE, INVALIDATE_ALL
from django_cache.models import CreatedCache
from django_cache.tasks import run_invalidate_task, relevance_invalidation_task

from example_apps.foo.models import Foo, Bar
from example_apps.foo.cache import (
    simple_foo, simple_bar, fast_foo_cache, fast_foo_timeout_cache,
    nested_foo_cache
)


class GeneralTestCase(TestCase):

    # def setUp(self):
    #     self.foo1 = Foo.objects.create(attr1=1, attr2="test1", attr3=1.1)
    #     self.foo2 = Foo.objects.create(attr1=2, attr2="test2", attr3=2.2)
    #     self.foo3 = Foo.objects.create(attr1=3, attr2="test3")

    def _setup_testing_data(self):
        foo1 = Foo.objects.create(attr1=1, attr2="test1", attr3=1.1)
        foo2 = Foo.objects.create(attr1=2, attr2="test2", attr3=2.2)
        foo3 = Foo.objects.create(attr1=3, attr2="test3")
        return foo1, foo2, foo3

    def test_simple_saving_and_getting(self):
        foo1, foo2, foo3 = self._setup_testing_data()
        kwargs = dict(attr1=foo1.attr1, attr2=foo1.attr2, attr3=foo1.attr3)
        res = list(simple_foo.save(**kwargs))
        self.assertEqual(list(simple_foo.get(**kwargs)), res)
        self.assertEqual(list(cache.get(simple_foo.get_key(**kwargs)).get("value")), res)

    def test_invalidation_change_fields(self):
        foo1, foo2, foo3 = self._setup_testing_data()
        kwargs1 = dict(attr1=foo1.attr1, attr2=foo1.attr2, attr3=foo1.attr3)
        kwargs2 = dict(attr1=foo2.attr1, attr2=foo2.attr2, attr3=foo2.attr3)
        simple_foo.save(**kwargs1)
        simple_foo.save(**kwargs2)
        self.assertIn(foo1, simple_foo.get(**kwargs1))
        self.assertNotIn(foo1, simple_foo.get(**kwargs2))
        for key, value in kwargs2.items():
            setattr(foo1, key, value)
        foo1.save()
        invalidate(simple_foo, kwargs1, kwargs2)
        self.assertNotIn(foo1, simple_foo.get(**kwargs1))
        self.assertIn(foo1, simple_foo.get(**kwargs2))
        cache.clear()

    def test_invalidation_field_was_empty(self):
        foo1, foo2, foo3 = self._setup_testing_data()
        kwargs2 = dict(attr1=foo2.attr1, attr2=foo2.attr2, attr3=foo2.attr3)
        kwargs3 = dict(attr1=foo3.attr1, attr2=foo3.attr2, attr3=foo3.attr3)
        simple_foo.save(**kwargs3)
        self.assertIn(foo3, simple_foo.get(**kwargs3))
        self.assertNotIn(foo3, simple_foo.get(**kwargs2))
        for key, value in kwargs2.items():
            setattr(foo3, key, value)
        foo3.save()
        invalidate(simple_foo, kwargs3, kwargs2)
        self.assertNotIn(foo3, simple_foo.get(**kwargs3))
        self.assertIn(foo3, simple_foo.get(**kwargs2))
        cache.clear()

    def test_invalidation_partial_changed_attrs(self):
        foo1 = Foo.objects.create(attr1=1, attr2="test", attr3=1.1)
        foo2 = Foo.objects.create(attr1=2, attr2="test")
        simple_foo.save(attr1=1, attr2="test", attr3=1.1)
        simple_foo.save(attr1=2, attr2="test", attr3=None)
        foo1.attr1 = 2
        foo1.attr3 = None
        foo1.save()
        invalidate(
            simple_foo,
            {"attr1": 1, "attr2": "test", "attr3": 1.1},
            {"attr1": 2, "attr2": "test", "attr3": None}
        )
        self.assertNotIn(foo1, simple_foo.get(attr1=1, attr2="test", attr3=1.1))
        self.assertIn(foo2, simple_foo.get(attr1=2, attr2="test", attr3=None))
        cache.clear()

    def test_invalidation_on_object_creation(self):
        foo1 = Foo.objects.create(attr1=1, attr2="test", attr3=1.1)
        simple_foo.save(attr1=1, attr2="test", attr3=1.1)
        self.assertIn(foo1, simple_foo.get(attr1=1, attr2="test", attr3=1.1))
        foo2 = Foo.objects.create(attr1=1, attr2="test", attr3=1.1)
        self.assertNotIn(foo2, simple_foo.get(attr1=1, attr2="test", attr3=1.1))
        invalidate(
            simple_foo,
            {"attr1": 1, "attr2": "test", "attr3": 1.1},
        )
        self.assertIn(foo2, simple_foo.get(attr1=1, attr2="test", attr3=1.1))
        cache.clear()

    def test_auto_invalidation(self):
        foo1 = Foo.objects.create(attr1=1, attr2="test", attr3=1.1)
        bar = Bar.objects.create(attr1=1, attr2="test", attr3=1.1, foo=foo1)
        self.assertIn(bar, simple_bar.get(attr1=1, attr2="test", attr3=1.1))
        bar2 = Bar.objects.create(attr1=1, attr2="test", attr3=1.1, foo=foo1)
        self.assertIn(bar2, simple_bar.get(attr1=1, attr2="test", attr3=1.1))
        bar3 = Bar.objects.create(attr1=2, attr2="test", attr3=1.1, foo=foo1)
        self.assertNotIn(bar3, simple_bar.get(attr1=1, attr2="test", attr3=1.1))
        bar3.attr1 = 1
        bar3.save()
        self.assertIn(bar3, simple_bar.get(attr1=1, attr2="test", attr3=1.1))
        bar3.delete()
        self.assertNotIn(bar3, simple_bar.get(attr1=1, attr2="test", attr3=1.1))
        cache.clear()

    def test_shortcuts(self):
        foo1 = Foo.objects.create(attr1=1, attr2="test", attr3=1.1)
        self.assertEqual(get_cache_worker("simple_foo"), simple_foo)
        self.assertIn(foo1, save_cache("simple_foo", attr1=1, attr2="test", attr3=1.1))
        self.assertIn(foo1, get_cache("simple_foo", attr1=1, attr2="test", attr3=1.1))
        # Work only with backend which support `delete_pattern`
        # clear_all("simple_foo")
        # self.assertNot(cache.get(get_cache_worker("simple_foo").key_gen(attr1=1, attr2="test", attr3=1.1)))
        foo2 = Foo.objects.create(attr1=1, attr2="test", attr3=1.1)
        self.assertNotIn(foo2, get_cache("simple_foo", attr1=1, attr2="test", attr3=1.1))
        invalidate_cache("simple_foo", old_data=dict(attr1=1, attr2="test", attr3=1.1))
        self.assertIn(foo2, get_cache("simple_foo", attr1=1, attr2="test", attr3=1.1))
        foo3 = Foo.objects.create(attr1=1, attr2="test", attr3=1.1)
        self.assertNotIn(foo3, get_cache("simple_foo", attr1=1, attr2="test", attr3=1.1))
        invalidate_all_cache("simple_foo")
        self.assertIn(foo3, get_cache("simple_foo", attr1=1, attr2="test", attr3=1.1))
        cache.clear()

    def test_task_body(self):
        kwargs = dict(attr1=1, attr2="test", attr3=1.1)
        foo1 = Foo.objects.create(**kwargs)
        self.assertIn(foo1, simple_foo.get(**kwargs))
        foo2 = Foo.objects.create(**kwargs)
        self.assertNotIn(foo2, simple_foo.get(**kwargs))
        run_invalidate_task(INVALIDATE, "simple_foo", outdated=kwargs)
        self.assertIn(foo2, simple_foo.get(**kwargs))
        foo3 = Foo.objects.create(**kwargs)
        self.assertNotIn(foo3, simple_foo.get(**kwargs))
        run_invalidate_task(INVALIDATE_ALL, "simple_foo")
        self.assertIn(foo3, simple_foo.get(**kwargs))
        cache.clear()

    def test_same_cache_object_cleaning(self):
        kwargs = dict(attr1=1, attr2="test", attr3=1.1)
        kwargs2 = dict(attr1=2, attr2="test2", attr3=2.1)
        foo1 = Foo.objects.create(**kwargs)
        foo2 = Foo.objects.create(**kwargs2)
        self.assertIn(foo1, simple_foo.get(**kwargs))
        c_object1 = CreatedCache.objects.first()
        self.assertIn(foo2, simple_foo.get(**kwargs2))
        c_object2 = CreatedCache.objects.last()
        self.assertEqual(CreatedCache.objects.count(), 2)
        foo3 = Foo.objects.create(**kwargs)
        self.assertIn(foo3, simple_foo.save(**kwargs))
        self.assertFalse(CreatedCache.objects.filter(id=c_object1.id).exists())
        self.assertTrue(CreatedCache.objects.filter(id=c_object2.id).exists())
        cache.clear()

    def test_lazy_invalidation(self):
        kwargs = dict(attr1=1, attr2="test", attr3=1.1)
        foo1 = Foo.objects.create(**kwargs)
        self.assertIn(foo1, fast_foo_cache.get(**kwargs))
        foo2 = Foo.objects.create(**kwargs)
        time.sleep(2)
        self.assertIn(foo2, fast_foo_cache.get(**kwargs))
        cache.clear()

    def test_timeout_invalidation(self):
        kwargs = dict(attr1=1, attr2="test", attr3=1.1)
        foo1 = Foo.objects.create(**kwargs)
        self.assertIn(foo1, fast_foo_timeout_cache.get(**kwargs))
        foo2 = Foo.objects.create(**kwargs)
        time.sleep(2)
        key = fast_foo_timeout_cache.get_key(**kwargs)
        self.assertNotIn(foo2, cache.get(key).get("value"))
        relevance_invalidation_task()
        self.assertIn(foo2, cache.get(key).get("value"))
        cache.clear()

    def test_nested_cache(self):
        kwargs = dict(attr1=1, attr2="test", attr3=1.1)
        foo1 = Foo.objects.create(**kwargs)
        foo2 = Foo.objects.create(**kwargs)
        bar1 = Bar.objects.create(foo=foo1, **kwargs)
        bar2 = Bar.objects.create(foo=foo1, **kwargs)
        self.assertIn(foo1, nested_foo_cache.get(attr1=1, bars=[bar1.id, bar2.id]))
        self.assertIn(foo1, nested_foo_cache.get(attr1=1, bars=[bar1.id]))
        bar2.foo = foo2
        bar2.save()
        self.assertNotIn(foo1, nested_foo_cache.get(attr1=1, bars=[bar2.id]))
        self.assertIn(foo2, nested_foo_cache.get(attr1=1, bars=[bar2.id]))
        self.assertIn(foo1, nested_foo_cache.get(attr1=1, bars=[bar1.id, bar2.id]))
        self.assertIn(foo2, nested_foo_cache.get(attr1=1, bars=[bar1.id, bar2.id]))
        bar2.foo = foo1
        bar2.save()
        self.assertIn(foo1, nested_foo_cache.get(attr1=1, bars=[bar2.id]))
        self.assertNotIn(foo2, nested_foo_cache.get(attr1=1, bars=[bar2.id]))
        self.assertIn(foo1, nested_foo_cache.get(attr1=1, bars=[bar1.id, bar2.id]))
        self.assertNotIn(foo2, nested_foo_cache.get(attr1=1, bars=[bar1.id, bar2.id]))
        cache.clear()

    def test_empty_attributes_cache(self):
        kwargs = dict(attr1=1, attr2="test", attr3=1.1)
        foo1 = Foo.objects.create(**kwargs)
        # Registered in settings
        self.assertIn(foo1, get_cache("all_foos"))
        foo2 = Foo.objects.create(**kwargs)
        self.assertIn(foo2, get_cache("all_foos"))
        cache.clear()
