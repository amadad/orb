"""
Activities package for Digital Being

Contains implementations of various activities that the digital being can perform.
"""

import sys
import os
from pathlib import Path

# Add the my_digital_being directory to sys.path
# This makes direct 'framework' imports work in activity files
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.append(str(parent_dir))
