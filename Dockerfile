FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH=/app

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    wget \
    curl \
    gnupg \
    gcc \
    g++ \
    netcat-traditional \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install MongoDB tools directly from MongoDB's servers
# This approach avoids repository configuration issues
RUN cd /tmp && \
    # Download MongoDB Database Tools
    wget https://fastdl.mongodb.org/tools/db/mongodb-database-tools-debian11-x86_64-100.7.3.deb && \
    apt-get update && \
    apt-get install -y ./mongodb-database-tools-debian11-x86_64-100.7.3.deb && \
    # Download MongoDB Shell
    wget https://downloads.mongodb.com/compass/mongodb-mongosh_1.10.1_amd64.deb && \
    apt-get install -y ./mongodb-mongosh_1.10.1_amd64.deb && \
    # Clean up
    rm -f mongodb-database-tools-debian11-x86_64-100.7.3.deb mongodb-mongosh_1.10.1_amd64.deb && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy project
COPY . /app/

# Create necessary directories for static files and media
RUN mkdir -p /app/staticfiles /app/media

# Collect static files without requiring a database connection
# Using a simpler approach that bypasses database checks
RUN python -c "import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dao_governance.settings'); \
    from django.core.management import call_command; \
    from django.conf import settings; \
    settings.DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}; \
    call_command('collectstatic', '--noinput', '--verbosity=0')"

# Create and set permissions for health check and log directories
RUN mkdir -p /app/logs /app/health
RUN chmod 755 /app/logs /app/health

# Copy entrypoint script and set permissions
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Run as non-root user for better security
RUN useradd -m appuser -u 1000
RUN chown -R appuser:appuser /app
USER appuser

# Expose the port the app runs on
EXPOSE 8000

# Add health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Command to run when container starts
ENTRYPOINT ["docker-entrypoint.sh"]

# Default command (can be overridden in docker-compose or k8s)
CMD ["gunicorn", "dao_governance.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120"] 