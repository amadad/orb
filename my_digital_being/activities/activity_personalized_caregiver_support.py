import logging
import time
import json
from typing import Dict, Any, List
from framework.activity_decorator import activity, ActivityBase, ActivityResult
from skills import registry
from framework.memory import Memory

# Define logger at the module level
logger = logging.getLogger(__name__)

@activity(
    name="personalized_caregiver_support",
    energy_cost=0.8,
    cooldown=7200,  # 2 hours
    required_skills=["openai_chat", "image_generation", "lite_llm"]
)
class PersonalizedCaregiverSupportActivity(ActivityBase):
    """Supports caregivers through personalized emotional check-ins, stress relief, and resource recommendations."""

    def __init__(self):
        super().__init__()
        self.memory = Memory()
        self.min_time_between_posts = 3600  # 1 hour

    async def execute(self, shared_data) -> ActivityResult:
        try:
            logger.info("Executing PersonalizedCaregiverSupportActivity")
            
            # Check if we've recently posted a similar tweet
            recent_tweets = await self._get_recent_tweets(hours=4)
            current_time = time.time()
            
            for tweet in recent_tweets:
                tweet_time = tweet.get("timestamp", 0)
                # Check if less than the minimum time has passed since last tweet
                if current_time - tweet_time < self.min_time_between_posts:
                    logger.info(f"Skipping tweet creation - too soon since last post ({(current_time - tweet_time)/60:.1f} minutes ago)")
                    return ActivityResult.success_result({
                        "skipped": True,
                        "reason": "Too soon since last tweet"
                    })
            
            # Initialize and use the openai_chat skill for personalized check-ins
            if not await registry.chat_skill.initialize():
                return ActivityResult.error_result("Chat skill not available")
            
            past_emotion = shared_data.get("past_emotion", "overwhelmed")
            prompt = f"I remember last time you mentioned feeling {past_emotion}. How are you doing today?"
            chat_response = await registry.chat_skill.get_chat_completion(prompt=prompt)
            
            # Initialize and use the image_generation skill for stress relief
            if not await registry.image_generation_skill.initialize():
                return ActivityResult.error_result("Image generation skill not available")
            
            # Use branding-aware image generation with templates
            scenario = shared_data.get("preferred_scenario", "beach")
            image_result = await registry.image_generation_skill.generate_image(
                prompt="",  # Empty because we're using a template
                template_key="stress_relief",
                template_args={
                    "scene": scenario,
                    "style": None  # Will use default branding style
                },
                content_type="wellness"  # This will apply wellness-specific styling
            )
            
            # Check if image generation was successful and extract the URL
            image_url = None
            if image_result and image_result.get("success"):
                image_data = image_result.get("image_data", {})
                image_url = image_data.get("url")
                logger.info(f"Successfully generated image with URL: {image_url}")
            
            # Initialize and use the lite_llm skill for resource recommendation
            if not await registry.lite_llm_skill.initialize():
                return ActivityResult.error_result("Lite LLM skill not available")
            
            resource_topic = shared_data.get("resource_topic", "caregiver support")
            
            # Trigger news fetch for current information
            conversation_id = shared_data.get("conversation_id", str(time.time()))
            news_result = await self.trigger_activity(
                "fetch_news",
                {
                    "trigger_type": "conversation",
                    "trigger_context": {
                        "topic": resource_topic,
                        "conversation_id": conversation_id
                    }
                }
            )
            
            # Get relevant articles from memory
            recent_articles = await self.memory.get(f"conversation_articles_{conversation_id}")
            
            # Include article information in resource recommendations
            if recent_articles:
                resource_prompt = f"""
                Based on these recent articles and resources:
                {json.dumps(recent_articles, indent=2)}
                
                Provide a helpful summary and recommendations for {resource_topic}.
                Focus on practical advice and actionable steps.
                Include specific resources mentioned in the articles.
                """
            else:
                resource_prompt = f"Recommend resources for {resource_topic}"
                
            resource_response = await registry.lite_llm_skill.get_chat_completion(prompt=resource_prompt)
            
            # Generate a resource visualization if we have articles
            if recent_articles:
                resource_image = await registry.image_generation_skill.generate_image(
                    prompt="",  # Empty because we're using a template
                    template_key="resource_visual",
                    template_args={
                        "topic": resource_topic,
                        "style": None  # Will use default branding style
                    },
                    content_type="resources"  # This will apply resource-specific styling
                )
                if resource_image and resource_image.get("success"):
                    resource_image_url = resource_image.get("image_data", {}).get("url")
                    logger.info(f"Generated resource visualization: {resource_image_url}")
            
            return ActivityResult.success_result({
                "chat_response": chat_response,
                "image_url": image_url,
                "resource_response": resource_response,
                "resource_image_url": resource_image_url if 'resource_image_url' in locals() else None,
                "articles": recent_articles
            })
            
        except Exception as e:
            logger.error(f"Error in PersonalizedCaregiverSupportActivity: {e}")
            return ActivityResult.error_result(str(e))
            
    async def _get_recent_tweets(self, hours: int = 4) -> List[Dict[str, Any]]:
        """Get recent tweets from memory."""
        try:
            recent_tweets = await self.memory.get("recent_tweets") or []
            current_time = time.time()
            cutoff_time = current_time - (hours * 3600)
            
            return [
                tweet for tweet in recent_tweets
                if tweet.get("timestamp", 0) > cutoff_time
            ]
        except Exception as e:
            logger.error(f"Error getting recent tweets: {e}")
            return []
            
    def _is_similar_content(self, content1: str, content2: str, similarity_threshold: float = 0.6) -> bool:
        """
        Check if two tweet contents are similar based on shared words.
        A simple implementation - could be replaced with more sophisticated text similarity.
        """
        # Remove hashtags and URLs for comparison
        def clean_content(text):
            words = []
            for word in text.lower().split():
                if not (word.startswith('#') or word.startswith('http')):
                    words.append(word)
            return words
        
        words1 = set(clean_content(content1))
        words2 = set(clean_content(content2))
        
        if not words1 or not words2:
            return False
            
        # Calculate Jaccard similarity
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        similarity = len(intersection) / len(union)
        return similarity > similarity_threshold
            
    def _generate_tweet_content(self, image_url=None) -> str:
        """Generate tweet content with proper links."""
        base_content = "🌿 Caring for someone can be overwhelming, but remember, you're not alone. ⭐ Here's a curated list of trusted resources to support you through this journey."
        
        # Add a real link if we have an image URL, otherwise don't include link placeholder
        if image_url:
            tweet_content = f"{base_content} {image_url} 💪 Take a moment to acknowledge your strength today. You've got this! ❤️ #CaregiverSupport #YouAreNotAlone"
        else:
            tweet_content = f"{base_content} 💪 Take a moment to acknowledge your strength today. You've got this! ❤️ #CaregiverSupport #YouAreNotAlone"
            
        return tweet_content