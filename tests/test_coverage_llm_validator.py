
import pytest
import json
import os
from unittest.mock import Mock, patch, AsyncMock
from llm_validator import LLMValidator

# Sample data
SAMPLE_ARTICLE = {
    'title': 'Test Article',
    'description': 'Test Description',
    'content': 'Test Content'
}

SAMPLE_ANALYSIS = {
    'gist': 'Test Gist',
    'sentiment': 'neutral',
    'tone': 'objective'
}

@pytest.mark.asyncio
class TestLLMValidatorCoverage:
    
    @pytest.fixture
    def validator(self):
        with patch.dict('os.environ', {'GROQ_API_KEY': 'test_key'}):
            return LLMValidator()

    async def test_json_cleanup_markdown(self, validator):
        """Test validation when LLM returns JSON wrapped in markdown code blocks."""
        # Case 1: ```json ... ```
        content_json_str = json.dumps({'is_valid': True, 'notes': 'Valid'})
        
        mock_create = AsyncMock()
        mock_choice = Mock()
        mock_choice.message.content = f'```json\n{content_json_str}\n```'
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        mock_create.return_value = mock_response
        
        validator.client.chat.completions.create = mock_create

        result = await validator.validate_analysis(SAMPLE_ARTICLE, SAMPLE_ANALYSIS)
        assert result['is_valid'] is True
        assert result['notes'] == 'Valid'

        # Case 2: ``` ... ``` (no language specifier)
        mock_choice.message.content = f'```\n{content_json_str}\n```'
        mock_create.return_value = mock_response # reset if needed, but it's same object ref
        
        validator.client.chat.completions.create = mock_create
        
        result = await validator.validate_analysis(SAMPLE_ARTICLE, SAMPLE_ANALYSIS)
        assert result['is_valid'] is True

    async def test_json_cleanup_extra_text(self, validator):
        """Test validation when LLM returns text alongside JSON."""
        content_json_str = json.dumps({'is_valid': True, 'notes': 'Valid'})
        
        mock_create = AsyncMock()
        mock_choice = Mock()
        mock_choice.message.content = f'   {content_json_str}   '
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        mock_create.return_value = mock_response
        
        validator.client.chat.completions.create = mock_create

        result = await validator.validate_analysis(SAMPLE_ARTICLE, SAMPLE_ANALYSIS)
        assert result['is_valid'] is True

    async def test_missing_required_fields(self, validator):
        """Test handling of JSON missing required fields."""
        mock_create = AsyncMock()
        mock_choice = Mock()
        mock_choice.message.content = json.dumps({'is_valid': True}) # Missing notes
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        mock_create.return_value = mock_response
        
        validator.client.chat.completions.create = mock_create
        
        result = await validator.validate_analysis(SAMPLE_ARTICLE, SAMPLE_ANALYSIS)
        
        # Should catch ValueError and return error dict
        assert result['is_valid'] is False
        assert "Validation failed due to error" in result['notes']
        assert "Missing required fields" in result['error']

    async def test_api_error_returns_failure(self, validator):
        """Test that API errors return a failure result instead of crashing."""
        mock_create = AsyncMock()
        mock_create.side_effect = Exception("Persistent Error")
        
        validator.client.chat.completions.create = mock_create
        
        result = await validator.validate_analysis(SAMPLE_ARTICLE, SAMPLE_ANALYSIS)
        
        assert result['is_valid'] is False
        assert "Validation failed" in result['notes']
