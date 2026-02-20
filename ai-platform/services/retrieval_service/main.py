import os
import sys
import asyncio
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import google.generativeai as genai

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from shared.vector_db.repository import QdrantRepository
from shared.logger.formatter import get_logger

app = FastAPI(title="Real-Time AI Intelligence Platform - Retrieval Service")
logger = get_logger("retrieval_service_main", "retrieval_service")

# Setup Gemini Config
genai.configure(api_key=os.getenv("GEMINI_API_KEY", "dummy_key_for_testing"))
vector_repo = QdrantRepository(collection_name="knowledge_base", vector_size=768)

@app.on_event("startup")
async def startup_event():
    await vector_repo.ensure_collection()
    logger.info("Retrieval Service initialized.")

class SearchRequest(BaseModel):
    query: str
    filter_map: Optional[Dict[str, Any]] = None
    limit: int = 5

class SearchResponse(BaseModel):
    results: List[Dict[str, Any]]

async def generate_embedding(text: str) -> list[float]:
    """Generates embedding vector utilizing Google Gemini's Embedding API."""
    def _embed():
         result = genai.embed_content(
            model="models/text-embedding-004",
            content=text,
            task_type="retrieval_query"
         )
         return result['embedding']
         
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _embed)

@app.post("/v1/search", response_model=SearchResponse)
async def semantic_search(request: SearchRequest):
    """Internal API to perform hybrid search against the Vector DB."""
    try:
        logger.info(f"Performing semantic search for query: '{request.query}' with filters: {request.filter_map}")
        
        # 1. Embed query
        query_vector = await generate_embedding(request.query)
        
        # 2. Search Qdrant
        results = await vector_repo.search_hybrid(
            query_vector=query_vector,
            filter_map=request.filter_map,
            limit=request.limit
        )
        
        return SearchResponse(results=results)
        
    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error during search")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "retrieval_service"}
