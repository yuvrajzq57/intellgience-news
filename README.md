# News Analysis Pipeline (v2)

An asynchronous dual-LLM pipeline for fetching, analyzing, and validating news articles.

## Overview
1.  **Fetch**: Retrieves articles from **NewsAPI** using `httpx`.
2.  **Analyze**: Uses **Groq (Llama 3.3 70B)** for sentiment, gist, and tone analysis.
3.  **Validate**: Uses **Groq (Llama 3.1 8B)** to fact-check and validate the primary analysis.
4.  **Interface**: Real-time streaming via **FastAPI (SSE)** or summarized CLI output.

## Architecture
- `pipeline.py`: Central `AsyncGenerator` orchestrating the flow.
- `api.py`: FastAPI server serving as the SSE production endpoint.
- `main.py`: CLI entry point for local execution and report generation.
- `news_fetcher.py`: Async client for NewsAPI integration.
- `llm_analyzer.py` / `llm_validator.py`: Groq model wrappers.

## Tech Stack
- **Runtime**: Python 3.10+ (AsyncIO)
- **Backend**: FastAPI & Uvicorn
- **LLMs**: Llama-3.3-70B (Analyzer) & Llama-3.1-8B (Validator)
- **Transport**: SSE (Server-Sent Events) for real-time logs

## Quick Start

### 1. Environment
```bash
# Requirements
pip install -r requirements.txt

# .env
NEWSAPI_KEY=your_key
GROQ_API_KEY=your_key
```

### 2. Execution
**API Mode (with SSE Streaming):**
```bash
python api.py
# Server starts at http://localhost:8000/api/analyze
```

**CLI Mode (Local Reports):**
```bash
python main.py
```

## Testing
```bash
pytest -v
```
