import os
import sys
import uuid
# Need to add root to PYTHONPATH for "shared" imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import FastAPI, Depends, Request
from pydantic import BaseModel
from typing import Dict, Any

from shared.kafka.client import KafkaProducerWrapper
from shared.schemas.events import UserEvent, IngestionEvent
from services.api_gateway.auth import verify_jwt, UserContext
from services.api_gateway.rate_limit import rate_limiter
from shared.logger.formatter import get_logger

app = FastAPI(title="Real-Time AI Intelligence Platform - API Gateway")
logger = get_logger("api_gateway_main", "api_gateway")

# Global dependencies
producer: KafkaProducerWrapper = None
KAFKA_BROKER = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
USER_EVENTS_TOPIC = os.getenv("KAFKA_USER_EVENTS_TOPIC", "user_events")
INGESTION_EVENTS_TOPIC = os.getenv("KAFKA_INGESTION_EVENTS_TOPIC", "ingestion_events")

@app.on_event("startup")
async def startup_event():
    global producer
    logger.info(f"Connecting to Kafka at {KAFKA_BROKER}")
    producer = KafkaProducerWrapper(bootstrap_servers=KAFKA_BROKER, client_id="api-gateway")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Flushing Kafka Producer...")
    if producer:
        await producer.flush()

class ActionRequest(BaseModel):
    action: str
    session_id: str
    payload: Dict[str, Any]

class IngestRequest(BaseModel):
    raw_text: str
    metadata: Dict[str, Any] = {}

@app.post("/v1/action")
@rate_limiter(requests_per_minute=100)
async def publish_user_action(
    request: Request, 
    action_req: ActionRequest, 
    user: UserContext = Depends(verify_jwt)
):
    """Publishes a structured user event to Kafka."""
    event = UserEvent(
        source="api_gateway",
        user_id=user.user_id,
        session_id=action_req.session_id,
        action=action_req.action,
        payload=action_req.payload
    )
    
    # Partition by user_id to ensure ordered event processing per user
    await producer.produce(topic=USER_EVENTS_TOPIC, key=user.user_id, value=event.model_dump(mode='json'))
    logger.info(f"Published user action {action_req.action} for user {user.user_id}")
    return {"status": "accepted", "event_id": event.event_id}

@app.post("/v1/ingest")
@rate_limiter(requests_per_minute=50)
async def publish_ingestion_event(
    request: Request, 
    ingest_req: IngestRequest, 
    user: UserContext = Depends(verify_jwt)
):
    """Receives unstructured text/data from client to be vectorized and processed."""
    event = IngestionEvent(
        source="api_gateway",
        raw_text=ingest_req.raw_text,
        metadata={**ingest_req.metadata, "uploaded_by_user_id": user.user_id}
    )
    
    # Random partition for ingestion loads or tie to source
    await producer.produce(topic=INGESTION_EVENTS_TOPIC, key=event.event_id, value=event.model_dump(mode='json'))
    logger.info(f"Published ingestion event {event.event_id}")
    return {"status": "accepted", "event_id": event.event_id}

@app.get("/health")
async def health_check():
    """Liveness probe end-point."""
    return {"status": "healthy", "service": "api_gateway"}
