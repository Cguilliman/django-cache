DATABASES = {
    'default': {
        # 'ENGINE': 'django.db.backends.sqlite3',
        # 'NAME': ':memory:',
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'test_django_cache',
        'USER': 'test_django_cache',
        'PASSWORD': 'test_django_cache',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

CACHES = {
    'default': {
        # This cache backend is OK to use in development and testing
        # but has the potential to break production setups with more than on process
        # due to each process having their own local memory based cache
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

SITE_ID = 1

MIDDLEWARE = [
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.admin',

    'example_apps.foo',
    'model_subscription',
    'django_cache',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

SECRET_KEY = 'too-secret-for-test'

USE_I18N = False

USE_L10N = False

USE_TZ = False

LOGIN_REDIRECT_URL = '/admin/'

ROOT_URLCONF = 'example_apps.urls'

# CELERY_ALWAYS_EAGER = True
# CELERY_TASK_ALWAYS_EAGER = True
# BROKER_BACKEND = 'memory'
CELERY_BROKER_URL = 'memory://'
# CELERY_BROKER_URL = 'amqp://guest:guest@rabbit:5672/%2F'


DJANGO_CACHE_WORKERS = {
    "all_foos": {
        "structure_getter": "example_apps.foo.getters.get_all_foo",
        "timeout": 10,
    },
}
