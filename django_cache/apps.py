from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class DjangoCacheConfig(AppConfig):
    name = 'django_cache'
    verbose_name = _('Cache')
