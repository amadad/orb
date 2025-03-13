import logging
from typing import Dict, Any
from framework.activity_decorator import activity, ActivityBase, ActivityResult
from skills import registry
from framework.memory import Memory

@activity(
    name="post_a_tweet",
    energy_cost=0.3,
    cooldown=14400,  # 4 hours
    required_skills=["x_api"]
)
class PostTweetActivity(ActivityBase):
    """Posts tweets to X (Twitter), including news and resources for caregivers."""
    
    def __init__(self):
        super().__init__()
        self.memory = Memory()

    async def execute(self, shared_data) -> ActivityResult:
        try:
            logger = logging.getLogger(__name__)
            logger.info("Starting tweet post activity")

            # Initialize X API skill
            if not await registry.x_api_skill.initialize():
                return ActivityResult.error_result("X API skill not available")

            # Check for queued news articles first
            shareable_articles = await self.memory.get("social_share_queue")
            
            if shareable_articles:
                # Get the first article
                article = shareable_articles[0]
                
                # Generate tweet content
                tweet_text = self._generate_news_tweet(article)
                
                # Post the tweet
                media_urls = [article.get('image_url')] if article.get('image_url') else None
                post_result = await registry.x_api_skill.post_tweet(tweet_text, media_urls)
                
                if post_result.get("success"):
                    # Remove the posted article from queue
                    shareable_articles.pop(0)
                    if shareable_articles:
                        await self.memory.store(
                            "social_share_queue",
                            shareable_articles,
                            ttl=43200  # Keep for 12 hours
                        )
                    else:
                        await self.memory.delete("social_share_queue")
                        
                    return ActivityResult.success_result({
                        "tweet_url": post_result.get("tweet_url"),
                        "content": tweet_text,
                        "type": "news",
                        "article": article
                    })
                else:
                    return ActivityResult.error_result(f"Failed to post tweet: {post_result.get('error')}")
            
            # If no news articles, proceed with regular tweet content
            tweet_text = shared_data.get("tweet_text")
            media_urls = shared_data.get("media_urls")
            
            if not tweet_text:
                return ActivityResult.error_result("No tweet content provided")
                
            post_result = await registry.x_api_skill.post_tweet(tweet_text, media_urls)
            
            if not post_result.get("success"):
                return ActivityResult.error_result(f"Failed to post tweet: {post_result.get('error')}")
                
            return ActivityResult.success_result({
                "tweet_url": post_result.get("tweet_url"),
                "content": tweet_text,
                "type": "regular"
            })

        except Exception as e:
            logger.error(f"Error in PostTweetActivity: {e}")
            return ActivityResult.error_result(str(e))
            
    def _generate_news_tweet(self, article: Dict[str, Any]) -> str:
        """Generate a tweet from a news article."""
        title = article.get('title', '')
        url = article.get('url', '')
        categories = article.get('categories', [])
        
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
        
        for category in categories:
            if category in category_to_hashtag:
                hashtags.append(category_to_hashtag[category])
        
        # Limit to 2 most relevant hashtags
        hashtags = hashtags[:2]
        
        # Construct tweet
        tweet_parts = []
        
        # Add title and URL
        if title and url:
            tweet_parts.append(f"📰 {title}")
            tweet_parts.append(url)
        
        # Add hashtags
        if hashtags:
            tweet_parts.append(" ".join(hashtags))
            
        # Add default hashtag if none from categories
        if not hashtags:
            tweet_parts.append("#CaregiverSupport")
            
        return " ".join(tweet_parts)
