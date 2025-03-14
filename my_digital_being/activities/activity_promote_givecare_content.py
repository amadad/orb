import logging
import time
import json
from typing import Dict, Any, List
from framework.activity_decorator import activity, ActivityBase, ActivityResult
from skills import registry
from framework.memory import Memory

@activity(
    name="promote_givecare_content",
    energy_cost=0.4,
    cooldown=86400,  # 24 hours
    required_skills=["serper_api", "chat_skill"]
)
class PromoteGiveCareContentActivity(ActivityBase):
    """
    Monitors and promotes GiveCare content, including news articles and resources.
    Handles both new content detection and strategic reposting of valuable older content.
    """

    def __init__(self):
        super().__init__()
        self.memory = Memory()
        # Store supported trigger types as class attribute
        self.supported_triggers = ["schedule", "manual"]
        # Parameters
        self.max_promotion_count = 5  # Max per day
        self.promotion_ratio = 0.3    # Ratio of new to reposted
        self.max_repost_age = 30      # Max age in days for reposting
        self.givecare_url = "https://www.givecareapp.com/news"
        self.categories = [
            "Product", "Advocacy", "Resources", 
            "PersonalWellness", "Community"
        ]
        self.min_repost_interval = 7 * 24 * 3600  # 7 days in seconds
        
    async def execute(self, shared_data) -> ActivityResult:
        try:
            logger = logging.getLogger(__name__)
            logger.info("Starting GiveCare content promotion activity")
            
            # Initialize Serper API skill
            if not await registry.serper_api_skill.initialize():
                return ActivityResult.error_result("Failed to initialize Serper API skill")

            # Check for new content
            new_articles = await self._fetch_new_articles()
            
            # Get previously promoted articles
            promoted_articles = await self.memory.get("givecare_promoted_articles") or []
            
            # Find articles we haven't promoted yet
            new_promotable_articles = [
                article for article in new_articles
                if not any(
                    pa["url"] == article["url"] 
                    for pa in promoted_articles
                )
            ]
            
            # Check if we should promote new content or repost existing
            if new_promotable_articles:
                # Prioritize new content
                article_to_promote = new_promotable_articles[0]
                promotion_type = "new"
            else:
                # Consider reposting older content
                article_to_promote = await self._select_article_for_repost(promoted_articles)
                promotion_type = "repost" if article_to_promote else None
            
            if not article_to_promote:
                return ActivityResult.success_result({
                    "status": "no_action",
                    "reason": "No suitable content for promotion at this time"
                })
            
            # Generate promotion content
            promotion_content = await self._generate_promotion_content(
                article_to_promote,
                promotion_type
            )
            
            # Queue for social sharing
            await self._queue_for_social_sharing(
                article_to_promote,
                promotion_content
            )
            
            # Update promotion history
            if promotion_type == "new":
                article_to_promote["first_promoted_at"] = time.time()
                article_to_promote["promotion_count"] = 1
                promoted_articles.append(article_to_promote)
            else:  # repost
                for article in promoted_articles:
                    if article["url"] == article_to_promote["url"]:
                        article["promotion_count"] = article.get("promotion_count", 1) + 1
                        article["last_promoted_at"] = time.time()
            
            # Store updated promotion history
            await self.memory.store(
                "givecare_promoted_articles",
                promoted_articles,
                ttl=None  # Store permanently
            )
            
            return ActivityResult.success_result({
                "status": "success",
                "promotion_type": promotion_type,
                "article": article_to_promote,
                "promotion_content": promotion_content
            })
            
        except Exception as e:
            logger.error(f"Error in PromoteGiveCareContentActivity: {e}")
            return ActivityResult.error_result(str(e))
            
    async def _fetch_new_articles(self) -> List[Dict[str, Any]]:
        """Fetch new articles from GiveCare news section."""
        try:
            # Search for GiveCare news articles
            result = await registry.serper_api_skill.search_news(
                query=f"site:{self.givecare_url}",
                num_results=10
            )
            
            if not result.get("success"):
                return []
                
            articles = result.get("articles", [])
            
            # Process and categorize articles
            processed_articles = []
            for article in articles:
                # Extract category from URL or title
                category = self._extract_category(article)
                if category:
                    article["category"] = category
                    processed_articles.append(article)
            
            return processed_articles
            
        except Exception as e:
            logging.error(f"Error fetching GiveCare articles: {e}")
            return []
            
    def _extract_category(self, article: Dict[str, Any]) -> str:
        """Extract article category from URL or title."""
        url = article.get("url", "").lower()
        title = article.get("title", "").lower()
        
        for category in self.categories:
            if category.lower() in url or category.lower() in title:
                return category
                
        return "General"
            
    async def _select_article_for_repost(self, promoted_articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Select an article for reposting based on various factors."""
        current_time = time.time()
        
        # Filter articles eligible for reposting
        eligible_articles = [
            article for article in promoted_articles
            if (
                # Not promoted in the last 7 days
                current_time - article.get("last_promoted_at", 0) >= self.min_repost_interval and
                # Not promoted more than 5 times
                article.get("promotion_count", 0) < 5
            )
        ]
        
        if not eligible_articles:
            return None
            
        # Initialize chat skill for content evaluation
        if not await registry.chat_skill.initialize():
            return eligible_articles[0]  # Fallback to first eligible if can't evaluate
            
        # Evaluate articles for reposting
        best_article = None
        best_score = -1
        
        for article in eligible_articles:
            prompt = f"""
            Evaluate this article's current relevance for reposting:
            Title: {article['title']}
            Description: {article['description']}
            Category: {article['category']}
            First posted: {time.ctime(article['first_promoted_at'])}
            Times shared: {article.get('promotion_count', 1)}
            
            Rate from 0.0 to 1.0 based on:
            1. Evergreen value
            2. Current relevance
            3. Engagement potential
            4. Time since last promotion
            
            Return only the numeric score.
            """
            
            try:
                response = await registry.chat_skill.get_chat_completion(prompt=prompt)
                score = float(response.strip())
                
                if score > best_score:
                    best_score = score
                    best_article = article
                    
            except (ValueError, Exception) as e:
                logging.error(f"Error evaluating article: {e}")
                continue
                
        return best_article
            
    async def _generate_promotion_content(self, 
                                        article: Dict[str, Any], 
                                        promotion_type: str) -> Dict[str, Any]:
        """Generate promotion content for the article."""
        try:
            if not await registry.chat_skill.initialize():
                return self._generate_default_promotion_content(article, promotion_type)
                
            prompt = f"""
            Generate engaging social media content for this article:
            Title: {article['title']}
            Description: {article['description']}
            Category: {article['category']}
            Type: {"New content" if promotion_type == "new" else "Valuable resource worth resharing"}
            
            Generate:
            1. Tweet text (max 280 chars)
            2. Three relevant hashtags
            
            Format: JSON with 'tweet' and 'hashtags' keys
            """
            
            response = await registry.chat_skill.get_chat_completion(prompt=prompt)
            try:
                content = json.loads(response)
                return {
                    "tweet_text": content["tweet"],
                    "hashtags": content["hashtags"][:3],
                    "url": article["url"],
                    "image_url": article.get("image_url")
                }
            except (json.JSONDecodeError, KeyError):
                return self._generate_default_promotion_content(article, promotion_type)
                
        except Exception as e:
            logging.error(f"Error generating promotion content: {e}")
            return self._generate_default_promotion_content(article, promotion_type)
            
    def _generate_default_promotion_content(self, 
                                          article: Dict[str, Any], 
                                          promotion_type: str) -> Dict[str, Any]:
        """Generate default promotion content if custom generation fails."""
        prefix = "📰 New from GiveCare: " if promotion_type == "new" else "📚 Must-read from GiveCare: "
        
        return {
            "tweet_text": f"{prefix}{article['title']}",
            "hashtags": ["#CaregiverSupport", "#GiveCare", f"#{article['category']}"],
            "url": article["url"],
            "image_url": article.get("image_url")
        }
            
    async def _queue_for_social_sharing(self, 
                                      article: Dict[str, Any], 
                                      promotion_content: Dict[str, Any]):
        """Queue the article for social media sharing."""
        tweet_content = (
            f"{promotion_content['tweet_text']} "
            f"{promotion_content['url']} "
            f"{' '.join(promotion_content['hashtags'])}"
        )
        
        await self.memory.store(
            "social_share_queue",
            [{
                "content": tweet_content,
                "title": article["title"],
                "url": article["url"],
                "image_url": promotion_content.get("image_url"),
                "category": article["category"],
                "queued_at": time.time(),
                "type": "givecare_promotion"
            }],
            ttl=43200  # Keep for 12 hours
        ) 