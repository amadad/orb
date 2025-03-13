"""
my_digital_being package

A sophisticated Python framework for creating intelligent digital entities with
advanced communication and dynamic skill management capabilities.
"""

import sys
import os

# Add the current directory to Python's module search path
# This makes 'framework' directly importable from activity modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from .framework.main import DigitalBeing
from .server import DigitalBeingServer

__version__ = "0.1.0"
__all__ = ["DigitalBeing", "DigitalBeingServer"]
