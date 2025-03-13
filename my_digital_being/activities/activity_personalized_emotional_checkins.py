import logging
from typing import Dict, Any
from framework.activity_decorator import activity, ActivityBase, ActivityResult
from skills.skill_chat import chat_skill
from framework.main import DigitalBeing

@activity(
    name="personalized_emotional_checkins",
    energy_cost=0.5,
    cooldown=3600,
    required_skills=["openai_chat"]
)
class PersonalizedEmotionalCheckinsActivity(ActivityBase):
    """Activity for sending personalized emotional check-in messages to caregivers"""

    def __init__(self):
        super().__init__()

    async def execute(self, shared_data) -> ActivityResult:
        try:
            logger = logging.getLogger(__name__)
            logger.info("Executing PersonalizedEmotionalCheckinsActivity")

            # Initialize the OpenAI chat skill
            if not await chat_skill.initialize():
                return ActivityResult.error_result("Chat skill not available")

            # Retrieve recent activities to tailor the message
            being = DigitalBeing()
            being.initialize()
            recent_activities = being.memory.get_recent_activities(limit=10)

            # Construct a personalized message for the caregiver
            prompt = (
                "Based on recent activities, create a personalized message "
                "for a caregiver acknowledging their stress levels and offering support."
            )
            response = await chat_skill.get_chat_completion(prompt=prompt)

            # Return the personalized message as the result
            return ActivityResult.success_result({"message": response})
        except Exception as e:
            logger.error(f"Error executing PersonalizedEmotionalCheckinsActivity: {e}")
            return ActivityResult.error_result(str(e))