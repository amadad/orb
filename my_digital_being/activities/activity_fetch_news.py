"""Activity for fetching news using web scraping."""

import logging
import time
import json
from typing import Dict, Any, List
from framework.activity_decorator import activity, ActivityBase, ActivityResult
from skills import registry
from framework.memory import Memory

logger = logging.getLogger(__name__)


@activity(
    name="fetch_news",
    energy_cost=0.5,
    cooldown=28800,  # 8 hours
    required_skills=["serper_api", "chat_skill"],
    triggers=["schedule", "conversation", "content_creation"]
)
class FetchNewsActivity(ActivityBase):
    """
    Fetches and processes news relevant to caregivers, storing useful information
    for other activities to reference.
    """

    def __init__(self):
        super().__init__()
        self.memory = Memory()
        self.default_topics = [
            "caregiver support resources",
            "caregiver wellness tips",
            "elderly care innovations",
            "caregiver mental health",
            "respite care services"
        ]
        
    async def _analyze_article_relevance(self, article: Dict[str, Any]) -> float:
        """Use chat skill to analyze article relevance for caregivers."""
        try:
            if not await registry.chat_skill.initialize():
                return 0.0
                
            prompt = f"""
            Analyze this article's relevance for caregivers:
            Title: {article['title']}
            Description: {article['description']}
            
            Rate from 0.0 to 1.0 based on:
            1. Direct usefulness for caregivers
            2. Actionable information
            3. Emotional support value
            4. Credibility of source
            
            Return only the numeric score.
            """
            
            response = await registry.chat_skill.get_chat_completion(prompt=prompt)
            try:
                score = float(response.strip())
                return min(max(score, 0.0), 1.0)  # Clamp between 0 and 1
            except ValueError:
                return 0.0
                
        except Exception as e:
            logging.error(f"Error analyzing article relevance: {e}")
            return 0.0

    async def _categorize_article(self, article: Dict[str, Any]) -> List[str]:
        """Categorize article into relevant topics."""
        try:
            if not await registry.chat_skill.initialize():
                return []
                
            prompt = f"""
            Categorize this article into relevant caregiver topics:
            Title: {article['title']}
            Description: {article['description']}
            
            Choose from these categories:
            - emotional_support
            - practical_tips
            - resources
            - health_advice
            - self_care
            - respite_care
            - technology
            - community
            
            Return only the category names, comma-separated.
            """
            
            response = await registry.chat_skill.get_chat_completion(prompt=prompt)
            return [cat.strip() for cat in response.split(',')]
            
        except Exception as e:
            logging.error(f"Error categorizing article: {e}")
            return []

    async def execute(self, shared_data) -> ActivityResult:
        try:
            logger = logging.getLogger(__name__)
            logger.info("Starting news fetch activity")

            # Get context from trigger
            trigger_type = shared_data.get("trigger_type", "schedule")
            trigger_context = shared_data.get("trigger_context", {})
            
            # Adjust topics based on trigger
            topics = self.default_topics.copy()
            if trigger_type == "conversation":
                conversation_topic = trigger_context.get("topic")
                if conversation_topic:
                    topics.append(f"caregiver {conversation_topic}")
            elif trigger_type == "content_creation":
                topics = [topic for topic in topics if "tips" in topic or "resources" in topic]

            # Initialize Serper API skill
            if not await registry.serper_api_skill.initialize():
                return ActivityResult.error_result("Failed to initialize Serper API skill")

            all_articles = []
            for topic in topics:
                result = await registry.serper_api_skill.search_news(
                    query=topic,
                    num_results=3  # Fetch more than needed for filtering
                )

                if result.get("success"):
                    articles = result.get("articles", [])
                    
                    # Process each article
                    for article in articles:
                        # Add relevance score
                        article['relevance_score'] = await self._analyze_article_relevance(article)
                        
                        # Add categories
                        article['categories'] = await self._categorize_article(article)
                        
                        # Add metadata
                        article['topic'] = topic
                        article['processed_timestamp'] = time.time()
                        
                        all_articles.append(article)

            # Filter and sort articles
            relevant_articles = [
                article for article in all_articles 
                if article['relevance_score'] >= 0.7  # Only keep highly relevant articles
            ]
            relevant_articles.sort(key=lambda x: x['relevance_score'], reverse=True)

            # Store in memory for other activities
            await self._store_articles_in_memory(relevant_articles)

            # Take actions based on trigger
            actions_taken = []
            if trigger_type == "conversation":
                await self._prepare_conversation_response(relevant_articles, trigger_context)
                actions_taken.append("prepared_conversation_response")
            elif trigger_type == "content_creation":
                await self._prepare_social_content(relevant_articles)
                actions_taken.append("prepared_social_content")

            return ActivityResult.success_result({
                "articles": relevant_articles,
                "topics": topics,
                "count": len(relevant_articles),
                "trigger_type": trigger_type,
                "actions_taken": actions_taken
            })

        except Exception as e:
            logger.error(f"Error in FetchNewsActivity: {e}")
            return ActivityResult.error_result(str(e))

    async def _store_articles_in_memory(self, articles: List[Dict[str, Any]]):
        """Store processed articles in memory for other activities to use."""
        try:
            # Store by category for easy retrieval
            for article in articles:
                for category in article['categories']:
                    await self.memory.store(
                        f"news_{category}",
                        article,
                        ttl=86400  # Keep for 24 hours
                    )
                    
            # Store full article list
            await self.memory.store(
                "recent_news",
                articles,
                ttl=86400
            )
            
        except Exception as e:
            logging.error(f"Error storing articles in memory: {e}")

    async def _prepare_conversation_response(self, articles: List[Dict[str, Any]], context: Dict[str, Any]):
        """Prepare articles for conversation responses."""
        try:
            topic = context.get("topic", "")
            relevant_articles = [
                article for article in articles
                if any(topic.lower() in cat.lower() for cat in article['categories'])
            ][:2]  # Get top 2 most relevant
            
            if relevant_articles:
                await self.memory.store(
                    f"conversation_articles_{context.get('conversation_id')}",
                    relevant_articles,
                    ttl=3600  # Keep for 1 hour
                )
            
        except Exception as e:
            logging.error(f"Error preparing conversation response: {e}")

    async def _prepare_social_content(self, articles: List[Dict[str, Any]]):
        """Prepare articles for social media content creation."""
        try:
            # Select top articles for social sharing
            shareable_articles = [
                article for article in articles
                if article['relevance_score'] >= 0.8 and
                any(cat in ['practical_tips', 'resources', 'self_care'] 
                    for cat in article['categories'])
            ][:3]  # Get top 3
            
            if shareable_articles:
                await self.memory.store(
                    "social_share_queue",
                    shareable_articles,
                    ttl=43200  # Keep for 12 hours
                )
            
        except Exception as e:
            logging.error(f"Error preparing social content: {e}")
