"""Drawing activity implementation."""

import logging
from typing import Dict, Any
from framework.activity_decorator import activity, ActivityBase, ActivityResult
from skills.skill_generate_image import ImageGenerationSkill
from framework.api_management import api_manager
from skills.skill_image_generation import image_generation_skill

logger = logging.getLogger(__name__)


@activity(
    name="draw",
    energy_cost=0.6,
    cooldown=3600, 
    required_skills=["image_generation"],
)
class DrawActivity(ActivityBase):
    def __init__(self):
        super().__init__()
        self.default_size = (1024, 1024)
        self.default_format = "png"

    async def execute(self, shared_data) -> ActivityResult:
        """Execute the drawing activity."""
        try:
            logger.info("Starting drawing activity")

            # First, initialize the skill
            if not await image_generation_skill.initialize():
                error_msg = "Failed to initialize image generation skill"
                logger.error(error_msg)
                return ActivityResult(success=False, error=error_msg)
                
            # Explicitly set enabled to True to ensure it can generate images
            image_generation_skill.enabled = True
            
            # Verify the skill can generate images
            if not await image_generation_skill.can_generate():
                error_msg = "Image generation is not available at this time"
                logger.error(error_msg)
                return ActivityResult(success=False, error=error_msg)

            # Generate drawing prompt
            prompt = self._generate_prompt(shared_data)

            # Generate the image
            result = await image_generation_skill.generate_image(
                prompt=prompt, size=self.default_size, format=self.default_format
            )

            if result.get("success"):
                # Store the generated image data
                if shared_data:
                    shared_data.set(
                        "memory",
                        f"drawing_{result['image_data']['generation_id']}",
                        {"prompt": prompt, "image_data": result["image_data"]},
                    )

                logger.info(f"Successfully generated image for prompt: {prompt}")
                return ActivityResult(
                    success=True,
                    data={
                        "generation_id": result["image_data"]["generation_id"],
                        "prompt": prompt,
                        "image_data": result["image_data"],
                    },
                    metadata={"size": self.default_size, "format": self.default_format},
                )
            else:
                error_msg = result.get("error", "Unknown error")
                logger.error(f"Failed to generate image: {error_msg}")
                return ActivityResult(success=False, error=error_msg)

        except Exception as e:
            logger.error(f"Failed to generate drawing: {e}")
            return ActivityResult(success=False, error=str(e))

    def _generate_prompt(self, shared_data) -> str:
        """Generate a drawing prompt based on current state and memory."""
        if shared_data:
            state = shared_data.get("state", "current_state", {})
            personality = state.get("personality", {})
            mood = state.get("mood", "neutral")
        else:
            # Default values if shared_data is None
            personality = {}
            mood = "neutral"

        # Base prompts for different moods
        mood_prompts = {
            "happy": "a sunny landscape with vibrant colors",
            "neutral": "a peaceful scene with balanced composition",
            "sad": "a rainy day with muted colors",
        }

        # Get base prompt from mood
        base_prompt = mood_prompts.get(mood, mood_prompts["neutral"])

        # Modify based on personality
        if personality.get("creativity", 0) > 0.7:
            base_prompt += " with surreal elements"
        if personality.get("curiosity", 0) > 0.7:
            base_prompt += " featuring unexpected details"

        return f"Digital artwork of {base_prompt}, digital art style"
