#!/bin/bash

echo "Starting Digital Being application"

# Create config directory if it doesn't exist
mkdir -p my_digital_being/config

# Start Gunicorn with our app
exec gunicorn app:app --bind=0.0.0.0:8000 