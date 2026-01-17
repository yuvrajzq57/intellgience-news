"""
Centralized pipeline logic for news analysis.
Used by both the API and CLI to ensure consistent behavior.
"""

import json
import logging
import asyncio
from typing import AsyncGenerator, List, Dict, Any

from news_fetcher import NewsFetcher
from llm_analyzer import LLMAnalyzer
from llm_validator import LLMValidator

logger = logging.getLogger(__name__)

class NewsAnalysisPipeline:
    """
    Orchestrates the fetching, analysis, and validation of news articles.
    Generates events for progress tracking.
    """
    
    def __init__(self):
        self.fetcher = NewsFetcher()
        self.analyzer = LLMAnalyzer()
        self.validator = LLMValidator()

    async def run(self, topic: str = "Indian Politics", count: int = 12) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Runs the full analysis pipeline and yields events.
        
        Events are dictionaries with 'event' and 'data' keys, suitable for SSE.
        """
        try:
            # --- Step 1: Initialization ---
            yield self._create_log_event(f"Initializing pipeline for '{topic}' ({count} articles)...", "fetch")
            await asyncio.sleep(0.1)

            # --- Step 2: Fetching ---
            yield self._create_log_event("Connecting to NewsAPI...", "fetch")
            
            # Fetching is now async in NewsFetcher
            articles = await self.fetcher.fetch_news(topic=topic, num_articles=count)
            
            if not articles:
                yield {
                    "event": "error",
                    "data": json.dumps({"message": "No articles found or API error."})
                }
                return

            yield self._create_log_event(f"Retrieved {len(articles)} articles successfully", "fetch")
            await asyncio.sleep(0.1)

            # --- Step 3: Analysis ---
            yield self._create_log_event("Starting LLM Analysis (Stage 1)...", "analyze")

            analysis_results = []
            
            for idx, article in enumerate(articles, 1):
                yield self._create_log_event(f"Analyzed article {idx}/{len(articles)}: Analyzing...", "analyze")
                
                # Run async analysis
                analysis = await self.analyzer.analyze_article(article)
                analysis_results.append({
                    'article': article,
                    'analysis': analysis
                })
                # Small delay to respect rate limits if needed, but not blocking logic
                await asyncio.sleep(0.5) 

            yield self._create_log_event("Analysis stage 1 complete - moving to validation", "analyze")

            # --- Step 4: Validation ---
            yield self._create_log_event("Starting LLM Validation (Stage 2)...", "validate")

            final_articles = []
            validated_results_full = [] # For CLI report generation if needed

            for idx, result in enumerate(analysis_results, 1):
                yield self._create_log_event(f"Validating article {idx}/{len(analysis_results)}...", "validate")
                
                validation = await self.validator.validate_analysis(
                    result['article'], 
                    result['analysis']
                )

                validated_results_full.append({
                    'article': result['article'],
                    'analysis': result['analysis'],
                    'validation': validation
                })

                # Format for frontend
                final_articles.append({
                    "id": idx,
                    "title": result['article']['title'],
                    "sentiment": result['analysis'].get('sentiment', 'neutral').lower(),
                    "validationPassed": validation.get('is_valid', False),
                    "validationNote": validation.get('notes', ''),
                    "summary": result['analysis'].get('gist', ''),
                    "url": result['article'].get('url', '#')
                })
                await asyncio.sleep(0.5)

            yield self._create_log_event("All articles validated successfully", "validate")
            
            # --- Step 5: Done ---
            yield self._create_log_event("Pipeline complete - results ready", "done")
            
            # Send final data
            yield {
                "event": "result",
                "data": json.dumps({"articles": final_articles})
            }
            
            # Send full detailed data (optional, useful for CLI saving files)
            yield {
                "event": "full_result",
                "data": json.dumps({"validated_results": validated_results_full, "raw_articles": articles})
            }

            # Close stream
            yield {
                "event": "close",
                "data": json.dumps({"message": "Stream closed"})
            }

        except Exception as e:
            logger.error(f"Error in pipeline: {e}")
            yield {
                "event": "error",
                "data": json.dumps({"message": f"Internal Server Error: {str(e)}"})
            }

    def _create_log_event(self, message: str, step: str) -> Dict[str, Any]:
        """Helper to create a log event."""
        return {
            "event": "log",
            "data": json.dumps({"message": message, "step": step})
        }
