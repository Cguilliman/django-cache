from django.contrib import admin

from .models import CreatedCache
from .contrib.invalidation import invalidate_created_caches
from .contrib.registration import workers_collection


def invalidate_action(modeladmin, request, queryset):
    for created_cache in queryset:
        worker = workers_collection.get(created_cache.label)
        if worker:
            invalidate_created_caches(created_cache, worker)


@admin.register(CreatedCache)
class CreatedCacheAdmin(admin.ModelAdmin):
    list_display = ("__str__", "created_at", "available_to", "relevance_to")
    readonly_fields = (
        "label", "created_at", "available_to",
        "relevance_to", "is_relevance_invalidation",
        "key", "attributes"
    )
    list_filter = ("created_at", "available_to", "relevance_to")
    actions = (invalidate_action, )
