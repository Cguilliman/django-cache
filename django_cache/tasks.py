from celery import shared_task

from .contrib.invalidation import INVALIDATION_PROCESSES, lazy_invalidation, invalidate_by_relevance_timeout
from .contrib.registration import workers_collection


@shared_task(default_retry_delay=1, max_retries=15)
def run_invalidate_task(invalidation_type, worker_label, *args, **kwargs):
    invalidation_func = INVALIDATION_PROCESSES.get(invalidation_type)
    invalidation_func(workers_collection.get(worker_label), *args, **kwargs)


@shared_task(default_retry_delay=1, max_retries=15)
def create_cache_log_task(key, timeout, label, is_timeout_invalidation, *args, **kwargs):
    from .contrib.save import log_cache_value
    log_cache_value(key, timeout, label, is_timeout_invalidation, *args, **kwargs)


@shared_task(default_retry_delay=5, max_retries=5)
def lazy_invalidation_task(key):
    lazy_invalidation(key)


@shared_task(default_retry_delay=1, max_retries=1)
def relevance_invalidation_task():
    invalidate_by_relevance_timeout()
