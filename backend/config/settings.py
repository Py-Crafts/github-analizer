"""
Django settings for GitHub Analyzer.

This file imports settings from the appropriate environment-specific module.
The settings are organized in a package structure:
- settings/base.py: Common settings
- settings/development.py: Development settings
- settings/production.py: Production settings
"""

# Import all settings from the settings package
from .settings import *