FROM python:3.11-slim

WORKDIR /app/my_digital_being

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

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
COPY requirements.txt /app/
RUN pip install -r /app/requirements.txt

# Copy the my_digital_being directory
COPY my_digital_being/ .

# Expose ports for web UI
EXPOSE 8000

CMD ["python", "server.py"]