#!/bin/sh

# use $PORT provided by Google Cloud Run if available
API_PORT=${API_PORT:-$PORT}
# Set the default port if no environment variable is provided
API_PORT=${API_PORT:-8080}

echo "Starting AI Bot Casino backend on port $API_PORT"

cd /app/

# Start the application with the given or default port
exec uvicorn main:app --host 0.0.0.0 --port $API_PORT
