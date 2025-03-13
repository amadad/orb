"""
Adapter module for image generation skill.
Provides backward compatibility with existing activities.
"""

import logging
from .skill_generate_image import ImageGenerationSkill

logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_CONFIG = {
    "enabled": True,
    "max_generations_per_day": 50,
    "supported_formats": ["png", "jpg"]
}

# Create a globally accessible instance
image_generation_skill = ImageGenerationSkill(DEFAULT_CONFIG)
logger.info("Initialized image_generation_skill adapter") 