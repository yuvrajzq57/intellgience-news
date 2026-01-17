"""
News fetcher module to retrieve articles from NewsAPI.
Handles API calls, rate limiting, and error handling.
"""

import os
import httpx
from datetime import datetime, timedelta
import asyncio
import logging

logger = logging.getLogger(__name__)

class NewsFetcher:
    """Fetches news articles from NewsAPI."""
    
    def __init__(self):
        """Initialize with API key from environment."""
        self.api_key = os.getenv('NEWSAPI_KEY')
        if not self.api_key:
            raise ValueError("NEWSAPI_KEY not found in environment variables")
        
        self.base_url = "https://newsapi.org/v2/everything"
        self.timeout = 10.0  # seconds
    
    async def fetch_news(self, topic="Indian Politics", num_articles=12):
        """
        Fetch recent news articles based on topic (Async).
        
        Args:
            topic: Topic to fetch (default: "Indian Politics")
            num_articles: Number of articles to fetch (default: 12)
            
        Returns:
            List of article dictionaries, or empty list on error
        """
        # Calculate date range (last 24 hours for realtime news)
        to_date = datetime.now()
        from_date = to_date - timedelta(days=1)
        
        # Topic mapping
        topic_queries = {
            "Indian Politics": "India politics OR India government",
            "Technology": "technology OR tech news OR artificial intelligence",
            "Business": "business OR economy OR market",
            "International": "international news OR world news"
        }
        
        query = topic_queries.get(topic, "India politics")
        
        params = {
            'q': query,
            'from': from_date.strftime('%Y-%m-%d'),
            'to': to_date.strftime('%Y-%m-%d'),
            'language': 'en',
            'sortBy': 'publishedAt',
            'pageSize': num_articles,
            'apiKey': self.api_key
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                print(f"  Requesting articles from NewsAPI...") # Keep print for CLI compatibility, or use logger
                response = await client.get(self.base_url, params=params)
                
                # Handle rate limiting
                if response.status_code == 429:
                    print("  Rate limit hit. Waiting 60 seconds...")
                    await asyncio.sleep(60)
                    response = await client.get(self.base_url, params=params)
                
                # Check for successful response
                response.raise_for_status()
                
                data = response.json()
                
                if data.get('status') != 'ok':
                    print(f"  API Error: {data.get('message', 'Unknown error')}")
                    return []
                
                articles = data.get('articles', [])
                
                # Clean and normalize articles
                cleaned_articles = []
                for article in articles:
                    # Skip articles without content
                    if not article.get('title') or not article.get('description'):
                        continue
                    
                    cleaned_article = {
                        'title': article.get('title', '').strip(),
                        'description': article.get('description', '').strip(),
                        'content': article.get('content', '').strip(),
                        'url': article.get('url', ''),
                        'publishedAt': article.get('publishedAt', ''),
                        'source': article.get('source', {}).get('name', 'Unknown')
                    }
                    cleaned_articles.append(cleaned_article)
                
                return cleaned_articles[:num_articles]
                
            except httpx.TimeoutException:
                print(f"  Request timed out after {self.timeout} seconds")
                return []
            
            except httpx.RequestError as e:
                print(f"  Request error: {str(e)}")
                return []
            
            except Exception as e:
                print(f"  Unexpected error: {str(e)}")
                return []
