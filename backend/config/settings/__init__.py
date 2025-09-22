"""
Settings package for GitHub Analyzer.

This package contains environment-specific settings:
- base.py: Common settings shared across all environments
- development.py: Development-specific settings
- production.py: Production-specific settings

The appropriate settings module is loaded based on the DJANGO_SETTINGS_MODULE
environment variable or the default development settings.
"""

import os
from decouple import config

# Determine which settings to use
ENVIRONMENT = config('ENVIRONMENT', default='development')

if ENVIRONMENT == 'production':
    from .production import *
elif ENVIRONMENT == 'development':
    from .development import *
else:
    # Default to development settings
    from .development import *