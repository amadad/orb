"""
Entrypoint file for the Digital Being server.
This file is used by gunicorn to run the server in production.
"""

import os
import sys

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the Flask app from the server module
from my_digital_being.server import app

# Start the server if run directly
if __name__ == "__main__":
    from my_digital_being.server import DigitalBeingServer
    import asyncio
    
    server = DigitalBeingServer()
    asyncio.run(server.start_server()) 