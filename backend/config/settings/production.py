"""
Production settings for GitHub Analyzer.
"""

from .base import *
import os
from decouple import config

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')

# Allowed hosts
ALLOWED_HOSTS = [
    'api.github-analyzer.com',
    'app.github-analyzer.com',
    'admin.github-analyzer.com',
    'github-analyzer.com',
    'www.github-analyzer.com',
    '127.0.0.1',
    'localhost',
]

# CORS settings for production
CORS_ALLOWED_ORIGINS = [
    "https://github-analyzer.com",
    "https://www.github-analyzer.com",
    "https://app.github-analyzer.com",
]

CORS_ALLOW_CREDENTIALS = True

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
USE_TZ = True

# Additional security headers
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='postgres'),
        'PORT': config('DB_PORT', default='5432'),
        'OPTIONS': {
            'sslmode': 'require',
        },
        'CONN_MAX_AGE': 600,
        'CONN_HEALTH_CHECKS': True,
    }
}

# Cache configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f"redis://{config('REDIS_HOST', default='redis')}:{config('REDIS_PORT', default='6379')}/1",
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            },
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
        },
        'KEY_PREFIX': 'github_analyzer',
        'TIMEOUT': 300,
    }
}

# Session configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_NAME = 'github_analyzer_sessionid'
SESSION_COOKIE_SAMESITE = 'Lax'

# CSRF configuration
CSRF_COOKIE_AGE = 31449600  # 1 year
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_NAME = 'github_analyzer_csrftoken'
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_TRUSTED_ORIGINS = [
    'https://github-analyzer.com',
    'https://www.github-analyzer.com',
    'https://app.github-analyzer.com',
    'https://api.github-analyzer.com',
]

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000

# Email configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@github-analyzer.com')
SERVER_EMAIL = config('SERVER_EMAIL', default='server@github-analyzer.com')

# Celery configuration for production
CELERY_BROKER_URL = f"redis://{config('REDIS_HOST', default='redis')}:{config('REDIS_PORT', default='6379')}/0"
CELERY_RESULT_BACKEND = f"redis://{config('REDIS_HOST', default='redis')}:{config('REDIS_PORT', default='6379')}/0"
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = True
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

# Celery Beat configuration
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/django/github_analyzer.log',
            'maxBytes': 1024*1024*15,  # 15MB
            'backupCount': 10,
            'formatter': 'json',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/django/github_analyzer_error.log',
            'maxBytes': 1024*1024*15,  # 15MB
            'backupCount': 10,
            'formatter': 'json',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console', 'file'],
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file', 'mail_admins'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['error_file', 'mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['error_file', 'mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'celery': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# REST Framework production settings
REST_FRAMEWORK.update({
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
        'login': '5/min',
        'analysis': '10/hour',
    },
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
})

# JWT settings for production
SIMPLE_JWT.update({
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'SIGNING_KEY': config('JWT_SIGNING_KEY', default=SECRET_KEY),
    'ALGORITHM': 'HS256',
})

# Performance optimizations
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Monitoring and health checks
HEALTH_CHECK = {
    'DISK_USAGE_MAX': 90,  # percent
    'MEMORY_MIN': 100,    # in MB
}

# Custom settings
GITHUB_API_BASE_URL = 'https://api.github.com'
GITHUB_API_TIMEOUT = 30
GITHUB_API_RATE_LIMIT_BUFFER = 100

# AI Provider settings
OPENAI_API_TIMEOUT = 60
ANTHROPIC_API_TIMEOUT = 60
AI_ANALYSIS_MAX_RETRIES = 3
AI_ANALYSIS_RETRY_DELAY = 5

# Export settings
EXPORT_FILE_RETENTION_DAYS = 7
EXPORT_MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
EXPORT_ALLOWED_FORMATS = ['xlsx', 'csv', 'json']

# Rate limiting for analysis tasks
ANALYSIS_RATE_LIMIT_PER_USER = 10  # concurrent tasks
ANALYSIS_RATE_LIMIT_PER_HOUR = 50  # per user per hour

# Monitoring
SENTRY_DSN = config('SENTRY_DSN', default='')
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.redis import RedisIntegration
    
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(
                transaction_style='url',
                middleware_spans=True,
                signals_spans=True,
            ),
            CeleryIntegration(
                monitor_beat_tasks=True,
            ),
            RedisIntegration(),
        ],
        traces_sample_rate=0.1,
        send_default_pii=False,
        environment='production',
        release=config('APP_VERSION', default='1.0.0'),
    )

# Admin settings
ADMIN_URL = config('ADMIN_URL', default='admin/')
ADMINS = [
    ('Admin', config('ADMIN_EMAIL', default='admin@github-analyzer.com')),
]
MANAGERS = ADMINS

# Backup settings
BACKUP_ENABLED = config('BACKUP_ENABLED', default=True, cast=bool)
BACKUP_SCHEDULE = config('BACKUP_SCHEDULE', default='0 2 * * *')  # Daily at 2 AM
BACKUP_RETENTION_DAYS = config('BACKUP_RETENTION_DAYS', default=30, cast=int)

# Feature flags
FEATURE_FLAGS = {
    'ENABLE_WEBHOOKS': config('ENABLE_WEBHOOKS', default=False, cast=bool),
    'ENABLE_ANALYTICS': config('ENABLE_ANALYTICS', default=True, cast=bool),
    'ENABLE_EXPORT_SCHEDULING': config('ENABLE_EXPORT_SCHEDULING', default=True, cast=bool),
    'ENABLE_TEAM_FEATURES': config('ENABLE_TEAM_FEATURES', default=True, cast=bool),
}