FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Create necessary directories if they don't exist
RUN mkdir -p my_digital_being/config my_digital_being/static my_digital_being/storage storage

# Copy application code
COPY . .

# Create a symbolic link for the entire storage directory
# This ensures files are accessible from both /app/storage and /app/my_digital_being/storage paths
# which is required by the application for proper OAuth file access
RUN rm -rf /app/storage && ln -sf /app/my_digital_being/storage /app/storage

# Create a health file in the static directory
RUN touch /app/my_digital_being/static/health

# Set environment variables
ENV PORT=8000
ENV PYTHONPATH=/app
ENV FLASK_APP=my_digital_being.server
ENV OAUTH_FILE_PATH=/app/my_digital_being/storage/composio_oauth.json

# Health check to ensure the application is responding
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/ || exit 1

# Expose the port
EXPOSE 8000

# Run the server directly with Python to enable both HTTP and WebSocket functionality
CMD ["python", "-m", "my_digital_being.server"]