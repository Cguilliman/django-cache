from example_apps.foo.models import Foo, Bar


def get_foo(attr1, attr2, attr3):
    return Foo.objects.filter(attr1=attr1, attr2=attr2, attr3=attr3)


def get_bar(**kwargs):
    return Bar.objects.filter(**kwargs)


def get_foo_with_nested(bars, attr1):
    return Foo.objects.filter(bars__in=bars, attr1=attr1).distinct()


def get_all_foo():
    return Foo.objects.all()