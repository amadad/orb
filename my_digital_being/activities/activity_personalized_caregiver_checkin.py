import logging
from typing import Dict, Any
from framework.activity_decorator import activity, ActivityBase, ActivityResult
from skills import registry  # Import the central registry

@activity(
    name="personalized_caregiver_checkin",
    energy_cost=0.7,
    cooldown=1800,
    required_skills=["openai_chat", "image_generation", "lite_llm"]
)
class PersonalizedCaregiverCheckin(ActivityBase):
    """Activity to provide personalized emotional check-ins, guided visualizations, and resource recommendations for caregivers"""

    def __init__(self):
        super().__init__()

    async def execute(self, shared_data: Dict[str, Any]) -> ActivityResult:
        try:
            logger = logging.getLogger(__name__)
            logger.info("Executing PersonalizedCaregiverCheckin")

            # Initialize and use the openai_chat skill for personalized emotional check-ins
            if not await registry.chat_skill.initialize():
                return ActivityResult.error_result("Chat skill not available")
            past_feeling = shared_data.get("last_feeling", "overwhelmed")
            chat_prompt = f"I remember last time you mentioned feeling {past_feeling}. How are you doing today?"
            chat_response = await registry.chat_skill.get_chat_completion(prompt=chat_prompt)

            # Initialize and use the image_generation skill for guided visualizations
            if not await registry.image_generation_skill.initialize():
                return ActivityResult.error_result("Image generation skill not available")
            visualization_response = await registry.image_generation_skill.generate_image(prompt="A serene beach or peaceful forest")

            # Initialize and use the lite_llm skill for resource recommendations
            if not await registry.lite_llm_skill.initialize():
                return ActivityResult.error_result("Lite LLM skill not available")
            resources_prompt = "Curate a list of resources for caregiver support, including articles, support groups, and professional services."
            resources_response = await registry.lite_llm_skill.get_chat_completion(prompt=resources_prompt)

            # Collect all results and return success
            result_data = {
                "chat_response": chat_response,
                "visualization_response": visualization_response,
                "resources": resources_response
            }
            return ActivityResult.success_result(result_data)

        except Exception as e:
            return ActivityResult.error_result(str(e))