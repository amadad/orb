"""
Digital Being application entry point
"""
import os
import sys

# Add the project directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Import the Flask app from the server module
from my_digital_being.server import app

# Start the server if run directly
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port) 