from django.db import models

from model_subscription.models import SubscriptionModelMixin, SubscriptionQuerySet


class Foo(SubscriptionModelMixin, models.Model):
    attr1 = models.IntegerField()
    attr2 = models.CharField(max_length=255)
    attr3 = models.FloatField(null=True, blank=True)

    objects = SubscriptionQuerySet.as_manager()


class Bar(SubscriptionModelMixin, models.Model):
    attr1 = models.IntegerField()
    attr2 = models.CharField(max_length=255)
    attr3 = models.FloatField(null=True, blank=True)
    foo = models.ForeignKey(Foo, on_delete=models.CASCADE, related_name='bars')

    objects = SubscriptionQuerySet.as_manager()
