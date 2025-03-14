import logging
from typing import Dict, Any
from framework.activity_decorator import activity, ActivityBase, ActivityResult
from skills.skill_chat import chat_skill
from skills.skill_image_generation import image_generation_skill
from skills.skill_lite_llm import lite_llm_skill

@activity(
    name="personalized_emotional_support",
    energy_cost=1.0,
    cooldown=7200,
    required_skills=["openai_chat", "image_generation", "lite_llm"]
)
class PersonalizedEmotionalSupportActivity(ActivityBase):
    """Activity designed for providing personalized emotional support to caregivers."""
    
    def __init__(self):
        super().__init__()

    async def execute(self, shared_data) -> ActivityResult:
        try:
            logger = logging.getLogger(__name__)
            logger.info("Executing PersonalizedEmotionalSupportActivity")

            # Initialize and use the openai_chat skill for emotional check-in
            if not await chat_skill.initialize():
                return ActivityResult.error_result("Chat skill not available")
            chat_prompt = "That sounds incredibly challenging. I'm here for you. How are you feeling today?"
            chat_response = await chat_skill.get_chat_completion(prompt=chat_prompt)

            # Initialize and use the image_generation skill for visual encouragements
            if not await image_generation_skill.initialize():
                return ActivityResult.error_result("Image generation skill not available")
            visual_message = "You are strong and resilient. Calming landscape."
            image_response = await image_generation_skill.generate_image(prompt=visual_message)

            # Initialize and use the lite_llm skill for resource navigation assistance
            if not await lite_llm_skill.initialize():
                return ActivityResult.error_result("Lite LLM skill not available")
            resource_prompt = "Guide me to credible resources for caregiver support."
            resource_response = await lite_llm_skill.get_chat_completion(prompt=resource_prompt)

            # Compile the results
            result_data = {
                "chat_response": chat_response,
                "image_url": image_response.get("image_url", "No image generated"),
                "resources": resource_response
            }
            return ActivityResult.success_result(result_data)
        except Exception as e:
            logger.error(f"Error executing activity: {str(e)}")
            return ActivityResult.error_result(str(e))