from django.db import models
from django.utils.translation import pgettext_lazy


class CreatedCache(models.Model):
    label = models.CharField(
        verbose_name=pgettext_lazy("cache", "Label"),
        max_length=255,
    )
    attributes = models.JSONField(
        verbose_name=pgettext_lazy("cache", "attributes")
    )
    key = models.CharField(
        verbose_name=pgettext_lazy("cache", "Key"),
        max_length=255,
    )
    created_at = models.DateTimeField(
        verbose_name=pgettext_lazy("cache", "Created At"),
        auto_now_add=True
    )
    is_relevance_invalidation = models.BooleanField(
        verbose_name=pgettext_lazy("cache", "Is timeout invalidation"),
        default=False
    )
    available_to = models.DateTimeField(
        verbose_name=pgettext_lazy("cache", "Available to"),
    )
    relevance_to = models.DateTimeField(
        verbose_name=pgettext_lazy("cache", "Relevance to"),
    )

    class Meta:
        verbose_name = pgettext_lazy("cache", "Created cache")
        verbose_name_plural = pgettext_lazy("cache", "Created caches")

    def __str__(self):
        return self.label
