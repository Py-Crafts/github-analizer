# Multi-stage Dockerfile for GitHub Analyzer Backend

# Base stage with common dependencies
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set work directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Development stage
FROM base as development

# Install development dependencies
RUN apt-get update && apt-get install -y \
    git \
    vim \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install development Python packages
RUN pip install --no-cache-dir \
    django-debug-toolbar \
    django-extensions \
    ipython \
    colorlog \
    python-json-logger

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/staticfiles /app/media /app/logs && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Default command for development
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# Production stage
FROM base as production

# Install production system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install production Python packages
RUN pip install --no-cache-dir \
    gunicorn \
    python-json-logger \
    sentry-sdk[django]

# Copy application code
COPY . .

# Create necessary directories and set permissions
RUN mkdir -p /app/staticfiles /app/media /var/log/django && \
    chown -R appuser:appuser /app /var/log/django && \
    chmod -R 755 /app && \
    chmod -R 755 /var/log/django

# Collect static files
RUN python manage.py collectstatic --noinput --settings=config.settings.production

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Production command with Gunicorn
CMD ["gunicorn", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--worker-class", "sync", \
     "--worker-connections", "1000", \
     "--max-requests", "1000", \
     "--max-requests-jitter", "100", \
     "--timeout", "30", \
     "--keep-alive", "2", \
     "--log-level", "info", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--capture-output", \
     "config.wsgi:application"]