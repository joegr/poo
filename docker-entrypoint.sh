#!/bin/bash
set -e

# Function to wait for a service to be ready
wait_for_service() {
    local host="$1"
    local port="$2"
    local service="$3"
    local max_attempts=30
    local attempt=1

    echo "Waiting for $service at $host:$port..."
    
    # Use nc from netcat-traditional package
    while ! nc -z -w 2 "$host" "$port" >/dev/null 2>&1; do
        if [ $attempt -ge $max_attempts ]; then
            echo "Error: $service is not available after $max_attempts attempts"
            exit 1
        fi
        
        echo "Attempt $attempt: $service is not available yet. Waiting..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "$service is available at $host:$port"
}

# Extract MongoDB host from URI
extract_mongo_host() {
    local uri="$1"
    local host=""
    
    # Try to extract host from standard MongoDB URI format
    if [[ "$uri" =~ mongodb://[^:]*:([^@]*)@([^:/]+) ]]; then
        host="${BASH_REMATCH[2]}"
    # Try alternative format
    elif [[ "$uri" =~ mongodb://([^:/]+) ]]; then
        host="${BASH_REMATCH[1]}"
    # Default to mongo service name if parsing fails
    else
        host="mongo"
    fi
    
    echo "$host"
}

# Wait for required services if in production/kubernetes environment
if [ "${KUBERNETES_SERVICE_HOST:-}" != "" ] || [ "${PRODUCTION:-}" = "True" ]; then
    # Extract host and port from environment variables
    POSTGRES_HOST=$(echo $DB_HOST | cut -d: -f1)
    POSTGRES_PORT=${DB_PORT:-5432}
    REDIS_PORT=${REDIS_PORT:-6379}
    
    # Wait for PostgreSQL
    wait_for_service "$POSTGRES_HOST" "$POSTGRES_PORT" "PostgreSQL"
    
    # Wait for Redis if used
    if [ -n "$REDIS_HOST" ]; then
        wait_for_service "$REDIS_HOST" "$REDIS_PORT" "Redis"
    fi
    
    # Wait for MongoDB if used
    if [ -n "$MONGO_URI" ]; then
        MONGO_HOST=$(extract_mongo_host "$MONGO_URI")
        MONGO_PORT=${MONGO_PORT:-27017}
        echo "Extracted MongoDB host: $MONGO_HOST"
        wait_for_service "$MONGO_HOST" "$MONGO_PORT" "MongoDB"
    fi
fi

# Apply database migrations
if [ "$1" = "gunicorn" ] || [ "$1" = "python" ] && [ "$2" = "manage.py" ] && [ "$3" = "runserver" ]; then
    echo "Applying database migrations..."
    python manage.py migrate --noinput
    
    # Create health check file
    echo "Creating health check file..."
    mkdir -p /app/health
    echo "OK" > /app/health/ready
fi

# Create log directory if it doesn't exist
mkdir -p /app/logs

# Handle different commands
if [ "$1" = "celery" ]; then
    echo "Starting Celery worker..."
    exec celery -A dao_governance worker -l INFO
elif [ "$1" = "celery-beat" ]; then
    echo "Starting Celery beat..."
    exec celery -A dao_governance beat -l INFO
elif [ "$1" = "flower" ]; then
    echo "Starting Flower monitoring..."
    exec celery -A dao_governance flower --port=5555
elif [ "$1" = "python" ] && [ "$2" = "manage.py" ] && [ "$3" = "shell" ]; then
    echo "Starting Django shell..."
    exec python manage.py shell
elif [ "$1" = "python" ] && [ "$2" = "manage.py" ] && [ "$3" = "dbshell" ]; then
    echo "Starting database shell..."
    exec python manage.py dbshell
else
    echo "Starting application with command: $@"
    exec "$@"
fi 