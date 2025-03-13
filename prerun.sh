#!/bin/bash
set -e

# Create necessary directories if they don't exist
mkdir -p my_digital_being/config
mkdir -p my_digital_being/static
mkdir -p my_digital_being/activities
mkdir -p my_digital_being/skills

# Set proper permissions
chmod -R 755 my_digital_being

# Set up environment if needed
if [ -f .env ]; then
  set -a
  source .env
  set +a
fi

echo "Prerun setup completed successfully"
exit 0 