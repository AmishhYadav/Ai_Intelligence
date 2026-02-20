import os
import sys
import asyncio
from typing import Any

# Add root to python path for shared modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from shared.kafka.client import KafkaConsumerWrapper
from shared.schemas.events import AlertEvent
from shared.logger.formatter import get_logger

logger = get_logger("alert_service_main", "alert_service")

KAFKA_BROKER = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
ALERTS_TOPIC = os.getenv("KAFKA_ALERTS_TOPIC", "alerts")

consumer = KafkaConsumerWrapper(bootstrap_servers=KAFKA_BROKER, group_id="alert-group", topics=[ALERTS_TOPIC])

async def dispatch_webhook(alert: AlertEvent):
    """Mocks sending a webhook payload to an external incident management system (e.g. PagerDuty)."""
    # In production, httpx.post(url, json=alert.model_dump())
    logger.warning(f"[EMAIL/WEBHOOK DISPATCHED] Severity: {alert.severity} | Message: {alert.message} | Context: {alert.context}")

async def process_alert(key: str, value: Any):
    try:
        alert = AlertEvent(**value)
        logger.info(f"Processing AlertEvent {alert.event_id}")
        
        # Route to relevant channels based on severity
        if alert.severity == "CRITICAL":
            await dispatch_webhook(alert)
        else:
            logger.info(f"[LOG ONLY ALERT] {alert.message}")
            
    except Exception as e:
        logger.error(f"Failed to process alert: {e}", exc_info=True)

async def main():
    logger.info("Starting Alert Service...")
    try:
        await consumer.consume_loop(process_alert)
    except KeyboardInterrupt:
        logger.info("Shutting down Alert Service...")
    finally:
        consumer.stop()

if __name__ == "__main__":
    asyncio.run(main())
