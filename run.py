"""
Digital Being application entry point
"""
import os
import uvicorn
from my_digital_being.server import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port) 