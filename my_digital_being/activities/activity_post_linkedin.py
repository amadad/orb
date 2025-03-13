"""LinkedIn posting activity implementation."""

import logging
from typing import Dict, Any, List
from framework.activity_decorator import activity, ActivityBase, ActivityResult
from framework.composio_integration import composio_manager
from framework.memory import Memory
from skills.skill_generate_image import ImageGenerationSkill

logger = logging.getLogger(__name__)

@activity(
    name="post_linkedin",
    energy_cost=0.4,
    cooldown=86400,  # 24 hours
    required_skills=["image_generation"]
)
class PostLinkedInActivity(ActivityBase):
    """Activity for posting content to LinkedIn company page."""

    COMPANY_URN = "urn:li:organization:106542185"  # GiveCare company URN

    def __init__(self):
        super().__init__()
        self.memory = Memory()
        self.image_skill = ImageGenerationSkill({
            "enabled": True,
            "max_generations_per_day": 50,
            "supported_formats": ["png", "jpg"]
        })

    async def execute(self, shared_data) -> ActivityResult:
        """Execute the LinkedIn posting activity."""
        try:
            logger.info("Starting LinkedIn posting activity")

            # First verify we can access the company page
            company_info = await composio_manager._toolset.execute_action(
                action="Get Company Info",
                params={
                    "organization_urn": self.COMPANY_URN
                },
                entity_id="MyDigitalBeing"
            )
            
            if not company_info.get("success", company_info.get("successfull")):
                return ActivityResult.error_result(f"Failed to verify LinkedIn company access for {self.COMPANY_URN}")

            # Check for queued news articles first
            content_data = await self._get_content_to_share()
            if not content_data:
                return ActivityResult.error_result("No content available to share")

            # Generate image using our branding system
            if not await self.image_skill.initialize():
                return ActivityResult.error_result("Image generation skill not available")

            # If we already have an image URL from the content, use that
            if content_data.get("image_url"):
                image_url = content_data["image_url"]
            else:
                # Generate a new image based on the content
                image_result = await self.image_skill.generate_image(
                    prompt="",  # Empty because we're using a template
                    template_key="resource_visual",
                    template_args={
                        "topic": content_data.get("topic", "caregiving support"),
                        "style": None  # Will use default branding style
                    },
                    content_type="resources"  # This will apply resource-specific styling
                )
                
                if not image_result.get("success"):
                    return ActivityResult.error_result("Failed to generate image")

                image_url = image_result.get("image_data", {}).get("url")
                if not image_url:
                    return ActivityResult.error_result("No image URL in generation result")

            # Generate post content
            post_content = self._format_linkedin_post(content_data)
            
            # Create LinkedIn post
            post_result = await composio_manager._toolset.execute_action(
                action="Create LinkedIn Post",
                params={
                    "organization_urn": self.COMPANY_URN,
                    "text": post_content,
                    "media_url": image_url
                },
                entity_id="MyDigitalBeing"
            )
            
            success = post_result.get("success", post_result.get("successfull"))
            if not success:
                error = post_result.get("error", "Unknown error")
                return ActivityResult.error_result(f"Failed to create LinkedIn post: {error}")

            # Update the social share queue if this was from news
            if content_data.get("source") == "news":
                await self._update_share_queue(content_data)

            logger.info(f"Successfully created LinkedIn post for {self.COMPANY_URN}")
            return ActivityResult.success_result({
                "post_id": post_result.get("data", {}).get("id"),
                "content": post_content,
                "image_url": image_url,
                "organization_urn": self.COMPANY_URN,
                "content_source": content_data.get("source"),
                "content_type": content_data.get("type")
            })
            
        except Exception as e:
            logger.error(f"Error in LinkedIn posting activity: {str(e)}")
            return ActivityResult.error_result(str(e))

    async def _get_content_to_share(self) -> Dict[str, Any]:
        """Get content to share from either news queue or recent tweets."""
        # First check news queue
        news_queue = await self.memory.get("social_share_queue")
        if news_queue and len(news_queue) > 0:
            article = news_queue[0]
            return {
                "source": "news",
                "type": "article",
                "title": article.get("title"),
                "description": article.get("description"),
                "url": article.get("url"),
                "image_url": article.get("image_url"),
                "categories": article.get("categories", []),
                "topic": article.get("topic", "caregiving")
            }

        # If no news, check recent tweets
        recent_tweets = await self.memory.get("recent_tweets")
        if recent_tweets and len(recent_tweets) > 0:
            tweet = recent_tweets[0]
            return {
                "source": "twitter",
                "type": "tweet",
                "content": tweet.get("content"),
                "image_url": tweet.get("image_url"),
                "topic": tweet.get("topic", "caregiving")
            }

        return None

    def _format_linkedin_post(self, content_data: Dict[str, Any]) -> str:
        """Format the LinkedIn post based on the content type."""
        if content_data["source"] == "news":
            return self._format_news_post(content_data)
        else:
            return self._format_tweet_post(content_data)

    def _format_news_post(self, article: Dict[str, Any]) -> str:
        """Format a news article for LinkedIn."""
        # Select appropriate hashtags based on categories
        hashtags = []
        category_to_hashtag = {
            'emotional_support': '#CaregiverSupport',
            'practical_tips': '#CaregivingTips',
            'resources': '#CareResources',
            'health_advice': '#CaregiverHealth',
            'self_care': '#SelfCare',
            'respite_care': '#RespiteCare',
            'technology': '#CaregivingTech',
            'community': '#CaregiverCommunity'
        }
        
        for category in article.get("categories", []):
            if category in category_to_hashtag:
                hashtags.append(category_to_hashtag[category])
        
        # Limit to 2 most relevant hashtags
        hashtags = hashtags[:2]
        if not hashtags:
            hashtags = ["#CaregiverSupport", "#Healthcare"]

        # Construct post
        post_parts = []
        
        # Add title and description
        if article.get("title"):
            post_parts.append(f"📰 {article['title']}")
        if article.get("description"):
            post_parts.append(f"\n\n{article['description']}")
        
        # Add URL if available
        if article.get("url"):
            post_parts.append(f"\n\nRead more: {article['url']}")
        
        # Add hashtags
        post_parts.append(f"\n\n{' '.join(hashtags)}")
            
        return "".join(post_parts)

    def _format_tweet_post(self, tweet_data: Dict[str, Any]) -> str:
        """Format a tweet for LinkedIn with additional context."""
        content = tweet_data.get("content", "")
        
        # Add LinkedIn-specific context and call-to-action
        post = f"{content}\n\n"
        post += "What are your thoughts on this? Share your caregiving experiences in the comments below. "
        post += "#CaregiverSupport #Healthcare #GiveCare"
        
        return post

    async def _update_share_queue(self, shared_content: Dict[str, Any]) -> None:
        """Update the social share queue after posting."""
        try:
            queue = await self.memory.get("social_share_queue") or []
            if queue:
                # Remove the shared content
                queue.pop(0)
                if queue:
                    # If there are more items, update the queue
                    await self.memory.store(
                        "social_share_queue",
                        queue,
                        ttl=43200  # Keep for 12 hours
                    )
                else:
                    # If queue is empty, delete it
                    await self.memory.delete("social_share_queue")
        except Exception as e:
            logger.error(f"Error updating share queue: {e}") 