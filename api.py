
import asyncio
import json
import logging
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

# Import existing modules
from pipeline import NewsAnalysisPipeline
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load env vars
load_dotenv()

app = FastAPI()

# Configure CORS
origins = [
    "http://localhost:3000",  # Frontend URL
    "http://127.0.0.1:3000",
    "https://news-article-opal.vercel.app/"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

@app.get("/api/analyze")
async def analyze_news(request: Request, topic: str = "Indian Politics", count: int = 12):
    """
    Streams analysis progress and results using Server-Sent Events (SSE).
    """
    async def event_generator() -> AsyncGenerator[dict, None]:
        pipeline = NewsAnalysisPipeline()
        
        async for event in pipeline.run(topic=topic, count=count):
            if await request.is_disconnected():
                logger.info("Client disconnected during analysis")
                break
                
            # Filter out 'full_result' as frontend might not need it, or keep it if it's lightweight.
            # actually frontend expects 'result', 'log', 'error', 'close'. 
            # 'full_result' is large and only for CLI saving really.
            if event['event'] == 'full_result':
                continue
                
            yield event

    return EventSourceResponse(event_generator())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
