import logging
import aiohttp
from typing import Dict, Any, List
from framework.api_management import api_manager

logger = logging.getLogger(__name__)

class SerperAPISkill:
    """Skill for fetching news using Serper.dev's Google Search API."""
    
    def __init__(self):
        self.skill_name = "serper_api"
        self.base_url = "https://google.serper.dev"
        self.api_key_name = "SERPER_API_KEY"
        self._initialized = False
        
    async def initialize(self) -> bool:
        """Initialize the Serper API skill."""
        try:
            self.api_key = await api_manager.get_api_key(self.skill_name, self.api_key_name)
            if not self.api_key:
                logger.error("No Serper API key available")
                return False
                
            self._initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Serper API skill: {e}")
            return False
            
    async def search_news(self, 
                         query: str,
                         num_results: int = 5) -> Dict[str, Any]:
        """Search for news articles using Serper's API."""
        if not self._initialized and not await self.initialize():
            return {"success": False, "error": "Serper API skill not initialized"}
            
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "X-API-KEY": self.api_key,
                    "Content-Type": "application/json"
                }
                
                # Use the news search endpoint
                url = f"{self.base_url}/news"
                params = {
                    "q": query,
                    "num": num_results
                }
                
                async with session.post(url, headers=headers, json=params) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"API error {response.status}: {error_text}")
                        
                    data = await response.json()
                    
                    # Transform to our standard format
                    articles = []
                    for news in data.get("news", []):
                        articles.append({
                            "title": news.get("title"),
                            "description": news.get("snippet"),
                            "url": news.get("link"),
                            "source": news.get("source"),
                            "published_at": news.get("date"),
                            "image_url": news.get("imageUrl")
                        })
                    
                    return {
                        "success": True,
                        "articles": articles
                    }
                    
        except Exception as e:
            logger.error(f"Error fetching news from Serper: {e}")
            return {
                "success": False,
                "error": str(e)
            }

# Create a global instance
serper_api_skill = SerperAPISkill() 