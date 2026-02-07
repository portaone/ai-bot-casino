FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Create non-root user for security
RUN useradd -m -s /bin/bash httpd
RUN usermod -aG root httpd

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Remove local config files - all config should come from environment variables
RUN rm -f /app/.env /app/.env_pydantic 2>/dev/null || true
RUN chmod 755 /app/start-web-server.sh

# Switch to non-root user
USER httpd

# Set environment variables
ARG API_PORT
ENV API_PORT=${API_PORT:-8080}
ENV PYTHONPATH=/app

# Expose port
EXPOSE $API_PORT

# Run the application
CMD ["/app/start-web-server.sh"]
