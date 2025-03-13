FROM --platform=linux/amd64 python:3.9-slim

WORKDIR /app

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Install basic dependencies
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    build-essential \
    curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install -r requirements.txt gunicorn

# Copy the entire application
COPY . .

# Create necessary directories
RUN mkdir -p my_digital_being/config my_digital_being/static my_digital_being/activities my_digital_being/skills

# Expose port for web UI
EXPOSE 8000

# Use a simpler command that's more likely to work
CMD gunicorn app:app --bind 0.0.0.0:8000