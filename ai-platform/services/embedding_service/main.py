import os
import sys
import asyncio
from typing import Any
import google.generativeai as genai

# Add root to python path for shared modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from shared.kafka.client import KafkaConsumerWrapper
from shared.schemas.events import EmbeddingJob
from shared.logger.formatter import get_logger
from shared.vector_db.repository import QdrantRepository

logger = get_logger("embedding_service_main", "embedding_service")

KAFKA_BROKER = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
EMBEDDING_TOPIC = os.getenv("KAFKA_EMBEDDING_JOBS_TOPIC", "embedding_jobs")

# Setup Gemini Config
genai.configure(api_key=os.getenv("GEMINI_API_KEY", "dummy_key_for_testing"))

consumer = KafkaConsumerWrapper(bootstrap_servers=KAFKA_BROKER, group_id="embedding-group", topics=[EMBEDDING_TOPIC])

# Gemini's embedding-001 or text-embedding-004 output 768 dimensions by default suitable for our default Qdrant settings
vector_repo = QdrantRepository(collection_name="knowledge_base", vector_size=768)

async def generate_embedding(text: str) -> list[float]:
    """Generates embedding vector utilizing Google Gemini's Embedding API."""
    def _embed():
         result = genai.embed_content(
            model="models/text-embedding-004",
            content=text,
            task_type="retrieval_document"
         )
         return result['embedding']
         
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _embed)

async def process_embedding_job(key: str, value: Any):
    """
    Consumes EmbeddingJob, generates embedding via Gemini, and stores it into Qdrant.
    """
    try:
        job = EmbeddingJob(**value)
        logger.info(f"Processing EmbeddingJob for document {job.document_id}")
        
        # 1. Generate Vector
        vector = await generate_embedding(job.text_content)
        
        # 2. Add raw text to payload for standard RAG retrieval
        payload = {
            **job.metadata,
            "text_content": job.text_content,
            "document_id": job.document_id
        }
        
        # 3. Upsert to Vector Database
        await vector_repo.upsert_vector(point_id=job.document_id, vector=vector, payload=payload)
        
        logger.info(f"Successfully embedded and saved document {job.document_id} to Qdrant.")

    except Exception as e:
        logger.error(f"Failed to process embedding job: {e}", exc_info=True)
        # If genai throws API error or Qdrant is down, this throws to consumer framework
        raise e

async def main():
    logger.info("Starting Embedding Service...")
    await vector_repo.ensure_collection()
    
    try:
        await consumer.consume_loop(process_embedding_job)
    except KeyboardInterrupt:
        logger.info("Shutting down Embedding Service...")
    finally:
        consumer.stop()

if __name__ == "__main__":
    asyncio.run(main())
