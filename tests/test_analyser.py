"""
Unit tests for the news analysis pipeline.
Tests core functionality without making actual API calls.
"""

import pytest
import json
import os
from unittest.mock import Mock, patch, AsyncMock
from news_fetcher import NewsFetcher
from llm_analyzer import LLMAnalyzer
from llm_validator import LLMValidator
import httpx

# Test data
SAMPLE_ARTICLE = {
    'title': 'India announces new economic policy',
    'description': 'The government unveiled a comprehensive economic reform package.',
    'content': 'India has announced major economic reforms...',
    'url': 'https://example.com/article',
    'publishedAt': '2024-01-15T10:00:00Z',
    'source': {'name': 'Test News'}
}

SAMPLE_ANALYSIS = {
    'gist': 'India announced major economic reforms to boost growth.',
    'sentiment': 'positive',
    'tone': 'analytical'
}

@pytest.mark.asyncio
class TestNewsFetcher:
    """Test the NewsFetcher class."""
    
    def test_fetcher_initialization_without_api_key(self):
        """Test that fetcher raises error without API key."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="NEWSAPI_KEY not found"):
                NewsFetcher()
    
    @patch('httpx.AsyncClient.get')
    async def test_successful_article_fetch(self, mock_get):
        """Test successful fetching of articles."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 'ok',
            'articles': [SAMPLE_ARTICLE]
        }
        mock_get.return_value = mock_response
        
        with patch.dict('os.environ', {'NEWSAPI_KEY': 'test_key'}):
            fetcher = NewsFetcher()
            articles = await fetcher.fetch_news(num_articles=1)
            
            assert len(articles) == 1
            assert articles[0]['title'] == SAMPLE_ARTICLE['title']
            assert 'source' in articles[0]
    
    @patch('httpx.AsyncClient.get')
    async def test_fetch_with_timeout(self, mock_get):
        """Test handling of timeout errors."""
        mock_get.side_effect = httpx.TimeoutException("Timeout")
        
        with patch.dict('os.environ', {'NEWSAPI_KEY': 'test_key'}):
            fetcher = NewsFetcher()
            articles = await fetcher.fetch_news()
            
            assert articles == []

@pytest.mark.asyncio
class TestLLMAnalyzer:
    """Test the LLMAnalyzer class."""
    
    def test_analyzer_initialization_without_api_key(self):
        """Test that analyzer raises error without API key."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="GROQ_API_KEY not found"):
                LLMAnalyzer()
    
    async def test_successful_analysis(self):
        """Test successful article analysis."""
        with patch.dict('os.environ', {'GROQ_API_KEY': 'test_key'}):
            analyzer = LLMAnalyzer()
            
            mock_create = AsyncMock()
            mock_choice = Mock()
            mock_choice.message.content = json.dumps(SAMPLE_ANALYSIS)
            mock_response = Mock()
            mock_response.choices = [mock_choice]
            mock_create.return_value = mock_response
            
            # We mock the client's method via instance replacement or patch?
            # Easiest is to replace the method on the instance, or `analyzer.client`.
            analyzer.client.chat.completions.create = mock_create
            
            result = await analyzer.analyze_article(SAMPLE_ARTICLE)
            
            assert 'gist' in result
            assert 'sentiment' in result
            assert 'tone' in result
            assert result['sentiment'] in ['positive', 'negative', 'neutral']

    async def test_analysis_with_json_error(self):
        """Test handling of malformed JSON response."""
        with patch.dict('os.environ', {'GROQ_API_KEY': 'test_key'}):
            analyzer = LLMAnalyzer()
            
            mock_create = AsyncMock()
            mock_choice = Mock()
            mock_choice.message.content = "This is not JSON"
            mock_response = Mock()
            mock_response.choices = [mock_choice]
            mock_create.return_value = mock_response
            
            analyzer.client.chat.completions.create = mock_create
            
            result = await analyzer.analyze_article(SAMPLE_ARTICLE)
            
            assert 'gist' in result
            assert 'error' in result or result['gist'] == 'Unable to analyze article'

@pytest.mark.asyncio
class TestLLMValidator:
    """Test the LLMValidator class."""
    
    def test_validator_initialization_without_api_key(self):
        """Test that validator raises error without API key."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="GROQ_API_KEY not found"):
                LLMValidator()
    
    async def test_successful_validation(self):
        """Test successful validation of analysis."""
        with patch.dict('os.environ', {'GROQ_API_KEY': 'test_key'}):
            validator = LLMValidator()
            
            mock_create = AsyncMock()
            mock_choice = Mock()
            mock_choice.message.content = json.dumps({
                'is_valid': True,
                'notes': 'Analysis is accurate and well-justified.'
            })
            mock_response = Mock()
            mock_response.choices = [mock_choice]
            mock_create.return_value = mock_response
            
            validator.client.chat.completions.create = mock_create
            
            result = await validator.validate_analysis(SAMPLE_ARTICLE, SAMPLE_ANALYSIS)
            
            assert 'is_valid' in result
            assert 'notes' in result
            assert isinstance(result['is_valid'], bool)
    
    async def test_validation_with_api_error(self):
        """Test handling of API errors during validation."""
        with patch.dict('os.environ', {'GROQ_API_KEY': 'test_key'}):
            validator = LLMValidator()
            
            mock_create = AsyncMock()
            mock_create.side_effect = Exception("API Error")
            validator.client.chat.completions.create = mock_create
            
            result = await validator.validate_analysis(SAMPLE_ARTICLE, SAMPLE_ANALYSIS)
            
            assert 'is_valid' in result
            assert result['is_valid'] is False
            assert 'error' in result

def test_article_data_structure():
    """Test that sample article has required fields."""
    required_fields = ['title', 'description', 'content', 'url', 'publishedAt', 'source']
    for field in required_fields:
        assert field in SAMPLE_ARTICLE, f"Missing required field: {field}"

def test_analysis_data_structure():
    """Test that sample analysis has required fields."""
    required_fields = ['gist', 'sentiment', 'tone']
    for field in required_fields:
        assert field in SAMPLE_ANALYSIS, f"Missing required field: {field}"