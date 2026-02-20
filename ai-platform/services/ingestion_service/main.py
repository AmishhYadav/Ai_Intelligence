import os
import sys
import asyncio
from typing import Any

# Add root to python path for shared modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from shared.kafka.client import KafkaConsumerWrapper, KafkaProducerWrapper
from shared.schemas.events import IngestionEvent, EmbeddingJob, ReasoningTask
from shared.logger.formatter import get_logger

logger = get_logger("ingestion_service_main", "ingestion_service")

KAFKA_BROKER = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
INGESTION_TOPIC = os.getenv("KAFKA_INGESTION_EVENTS_TOPIC", "ingestion_events")
EMBEDDING_TOPIC = os.getenv("KAFKA_EMBEDDING_JOBS_TOPIC", "embedding_jobs")
REASONING_TOPIC = os.getenv("KAFKA_REASONING_TASKS_TOPIC", "reasoning_tasks")

producer = KafkaProducerWrapper(bootstrap_servers=KAFKA_BROKER, client_id="ingestion-producer")
consumer = KafkaConsumerWrapper(bootstrap_servers=KAFKA_BROKER, group_id="ingestion-group", topics=[INGESTION_TOPIC])

async def process_ingestion_event(key: str, value: Any):
    """
    Validates the IngestionEvent, performs sanitization, and routes to downstream topics.
    """
    try:
        # Schema validation via Pydantic
        event = IngestionEvent(**value)
        
        # Output document ID is tied to the original event ID for traceability
        document_id = event.event_id
        sanitized_text = event.raw_text.strip()
        
        logger.info(f"Processing IngestionEvent {event.event_id} from user {event.metadata.get('uploaded_by_user_id')}")

        # 1. Route to Embedding Service
        embedding_job = EmbeddingJob(
            source="ingestion_service",
            document_id=document_id,
            text_content=sanitized_text,
            metadata=event.metadata
        )
        
        # 2. Route to Reasoning Service to summarize/analyze the new document automatically
        reasoning_task = ReasoningTask(
            source="ingestion_service",
            user_id=event.metadata.get("uploaded_by_user_id", "system"),
            session_id=event.metadata.get("session_id", "default_session"),
            query=f"Analyze the recently ingested document: {document_id}",
            context_keys=[document_id] # Pass reference to newly embedding document
        )

        # Publish concurrently
        await asyncio.gather(
            producer.produce(EMBEDDING_TOPIC, key=document_id, value=embedding_job.model_dump(mode='json')),
            producer.produce(REASONING_TOPIC, key=reasoning_task.session_id, value=reasoning_task.model_dump(mode='json'))
        )
        
        logger.info(f"Successfully routed jobs for document {document_id}")

    except Exception as e:
        logger.error(f"Failed to process ingestion event: {e}", exc_info=True)
        raise e  # Let the consumer error handler manage it

async def main():
    logger.info("Starting Ingestion Service...")
    try:
        await consumer.consume_loop(process_ingestion_event)
    except KeyboardInterrupt:
        logger.info("Shutting down Ingestion Service...")
    finally:
        consumer.stop()
        await producer.flush()

if __name__ == "__main__":
    asyncio.run(main())
