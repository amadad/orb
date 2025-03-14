"""Image generation skill implementation."""

import logging
from typing import Dict, Any, Tuple, Optional
import random
import os
import openai
from openai import OpenAI
import asyncio
from framework.api_management import api_manager
from config.branding import IMAGE_GENERATION, get_image_style, format_image_prompt

logger = logging.getLogger(__name__)


class ImageGenerationSkill:
    def __init__(self, config: Dict[str, Any]):
        """Initialize the image generation skill with secure API key handling."""
        self.enabled = config.get("enabled", False)
        logger.info(f"ImageGenerationSkill initialized with enabled={self.enabled}")
        self.max_generations = config.get("max_generations_per_day", 50)
        self.supported_formats = config.get("supported_formats", ["png", "jpg"])
        self.generations_count = 0
        self.branding = IMAGE_GENERATION

        # Register required API keys
        api_manager.register_required_keys("image_generation", ["OPENAI"])
        
        self._initialized = False
        self._api_key = None

    async def initialize(self) -> bool:
        """Initialize the skill by loading the API key."""
        try:
            # Verify API key exists and is configured
            self._api_key = await api_manager.get_api_key("image_generation", "OPENAI")
            if not self._api_key:
                logger.error("OpenAI API key not configured for image generation")
                return False
                
            self._initialized = True
            logger.debug(f"Image generation skill initialized successfully. enabled={self.enabled}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize image generation skill: {e}")
            return False

    async def can_generate(self) -> bool:
        """Check if image generation is allowed."""
        if not self._initialized:
            logger.warning("Image generation skill not initialized")
            return False
            
        if not self.enabled:
            logger.warning(f"Image generation is disabled (enabled={self.enabled})")
            return False

        if self.generations_count >= self.max_generations:
            logger.warning("Daily generation limit reached")
            return False

        logger.debug(f"Image generation is allowed (enabled={self.enabled}, generations={self.generations_count}/{self.max_generations})")
        return True

    def _enhance_prompt(self, prompt: str, content_type: Optional[str] = None) -> str:
        """Enhance the prompt with branding elements."""
        if content_type:
            style = get_image_style(content_type)
        else:
            style = self.branding["base_style"]
            
        # Add common elements for consistency
        common_elements = self.branding["common_elements"]
        enhanced_prompt = (
            f"{prompt}, "
            f"{style}, "
            f"lighting: {common_elements['lighting']}, "
            f"{common_elements['composition']}, "
            f"{common_elements['mood']}"
        )
        
        return enhanced_prompt

    async def generate_image(
        self, 
        prompt: str, 
        size: Tuple[int, int] = (1024, 1024), 
        format: str = "png",
        content_type: Optional[str] = None,
        template_key: Optional[str] = None,
        template_args: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate an image based on the prompt."""
        if not self._initialized and not await self.initialize():
            error_msg = "Image generation skill not initialized"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
            
        if not await self.can_generate():
            error_msg = "Image generation is not available (disabled, limit reached, or not configured)"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

        if format not in self.supported_formats:
            error_msg = f"Unsupported format. Use: {self.supported_formats}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

        try:
            # If a template is provided, use it to format the prompt
            if template_key and template_args:
                prompt = format_image_prompt(template_key, **template_args)
            
            # Enhance the prompt with branding elements
            enhanced_prompt = self._enhance_prompt(prompt, content_type)
            logger.info(f"Enhanced prompt: {enhanced_prompt}")
            
            # Configure OpenAI with the retrieved API key
            os.environ["OPENAI_API_KEY"] = self._api_key

            client = OpenAI()

            # Map the size tuple to OpenAI's expected string format
            size_str = f"{size[0]}x{size[1]}"

            logger.info(f"Generating image with size {size_str}")

            # As OpenAI's library is synchronous, run it in a separate thread to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.images.generate(
                    model="dall-e-3",
                    prompt=enhanced_prompt,
                    n=1,
                    size=size_str,
                    response_format="url",  # You can change to "b64_json" if needed
                ),
            )

            # Extract the image URL from the response
            image_url = response.data[0].url

            # Increment counter only on successful generation
            self.generations_count += 1

            # Generate a seed and generation_id for consistency with previous structure
            seed = random.randint(1000, 9999)
            generation_id = f"gen_{self.generations_count}"

            image_data = {
                "width": size[0],
                "height": size[1],
                "format": format,
                "seed": seed,
                "generation_id": generation_id,
                "url": image_url,  # Including the actual image URL from OpenAI
            }

            return {
                "success": True,
                "image_data": image_data,
                "metadata": {
                    "prompt": prompt,
                    "enhanced_prompt": enhanced_prompt,
                    "content_type": content_type,
                    "generation_number": self.generations_count,
                },
            }

        except Exception as e:
            logger.error(f"Failed to generate image: {e}")
            return {"success": False, "error": str(e)}

    def reset_counts(self):
        """Reset the generation counter."""
        self.generations_count = 0
