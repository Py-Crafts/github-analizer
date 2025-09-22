"""
Development settings for GitHub Analyzer.
"""

from .base import *
import os
from decouple import config

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-dev-key-change-in-production')

# Allowed hosts for development
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '0.0.0.0',
    '[::1]',
]

# CORS settings for development
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# Database for development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Alternative PostgreSQL configuration for development
# Uncomment if you want to use PostgreSQL in development
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': config('DB_NAME', default='github_analyzer_dev'),
#         'USER': config('DB_USER', default='postgres'),
#         'PASSWORD': config('DB_PASSWORD', default='postgres'),
#         'HOST': config('DB_HOST', default='localhost'),
#         'PORT': config('DB_PORT', default='5432'),
#     }
# }

# Cache configuration for development
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Alternative Redis cache for development
# Uncomment if you want to use Redis in development
# CACHES = {
#     'default': {
#         'BACKEND': 'django_redis.cache.RedisCache',
#         'LOCATION': f"redis://{config('REDIS_HOST', default='localhost')}:{config('REDIS_PORT', default='6379')}/1",
#         'OPTIONS': {
#             'CLIENT_CLASS': 'django_redis.client.DefaultClient',
#         },
#         'KEY_PREFIX': 'github_analyzer_dev',
#         'TIMEOUT': 300,
#     }
# }

# Session configuration for development
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_COOKIE_SECURE = False
SESSION_COOKIE_HTTPONLY = True

# CSRF configuration for development
CSRF_COOKIE_SECURE = False

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Email backend for development (console)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'noreply@localhost'

# Celery configuration for development
CELERY_TASK_ALWAYS_EAGER = config('CELERY_ALWAYS_EAGER', default=False, cast=bool)
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')

# If using in-memory broker for development
if config('USE_MEMORY_BROKER', default=False, cast=bool):
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True

# Development-specific apps
INSTALLED_APPS += [
    'django_extensions',  # Provides shell_plus and other useful commands
]

# REST Framework settings for development
REST_FRAMEWORK.update({
    'DEFAULT_THROTTLE_CLASSES': [],  # Disable throttling in development
    'DEFAULT_THROTTLE_RATES': {},
})

# JWT settings for development
SIMPLE_JWT.update({
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=24),  # Longer tokens for development
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'SIGNING_KEY': SECRET_KEY,
})

# Logging configuration for development
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
        'colored': {
            '()': 'colorlog.ColoredFormatter',
            'format': '%(log_color)s%(levelname)-8s%(reset)s %(blue)s%(message)s',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'colored',
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'debug.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console'],
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG' if config('DEBUG_SQL', default=False, cast=bool) else 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'celery': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Create logs directory if it doesn't exist
os.makedirs(BASE_DIR / 'logs', exist_ok=True)

# Development-specific settings
INTERNAL_IPS = [
    '127.0.0.1',
    'localhost',
]

# Django Debug Toolbar (optional)
if config('USE_DEBUG_TOOLBAR', default=False, cast=bool):
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE = ['debug_toolbar.middleware.DebugToolbarMiddleware'] + MIDDLEWARE

# Custom settings for development
GITHUB_API_RATE_LIMIT_BUFFER = 50  # Lower buffer for development

# AI Provider settings for development
AI_ANALYSIS_MAX_RETRIES = 1  # Fewer retries in development
AI_ANALYSIS_RETRY_DELAY = 2  # Shorter delay

# Export settings for development
EXPORT_FILE_RETENTION_DAYS = 1  # Shorter retention for development
EXPORT_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB for development

# Analysis settings for development
ANALYSIS_RATE_LIMIT_PER_USER = 10  # More lenient in development
ANALYSIS_RATE_LIMIT_PER_HOUR = 100  # More lenient in development

# Feature flags for development
FEATURE_FLAGS = {
    'ENABLE_WEBHOOKS': config('ENABLE_WEBHOOKS', default=True, cast=bool),
    'ENABLE_ANALYTICS': config('ENABLE_ANALYTICS', default=True, cast=bool),
    'ENABLE_EXPORT_SCHEDULING': config('ENABLE_EXPORT_SCHEDULING', default=True, cast=bool),
    'ENABLE_TEAM_FEATURES': config('ENABLE_TEAM_FEATURES', default=True, cast=bool),
    'ENABLE_DEBUG_FEATURES': True,
}

# Development tools
SHELL_PLUS_PRINT_SQL = config('SHELL_PLUS_PRINT_SQL', default=False, cast=bool)
SHELL_PLUS_PRINT_SQL_TRUNCATE = 1000

# API Documentation settings
SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header'
        }
    },
    'USE_SESSION_AUTH': False,
    'JSON_EDITOR': True,
    'SUPPORTED_SUBMIT_METHODS': [
        'get',
        'post',
        'put',
        'delete',
        'patch'
    ],
}

# Disable security features for development
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SECURE_CONTENT_TYPE_NOSNIFF = False
SECURE_BROWSER_XSS_FILTER = False