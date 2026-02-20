import json
import logging
import asyncio
from typing import Callable, Awaitable, Any, Optional, List
from confluent_kafka import Producer, Consumer, KafkaError

logger = logging.getLogger(__name__)

class KafkaProducerWrapper:
    """Async wrapper for Confluent Kafka Producer featuring idempotence and non-blocking IO."""
    def __init__(self, bootstrap_servers: str, client_id: str):
        self.conf = {
            'bootstrap.servers': bootstrap_servers,
            'client.id': client_id,
            'enable.idempotence': True, # Idempotent producer
            'acks': 'all',
            'retries': 5
        }
        self.producer = Producer(self.conf)

    def delivery_report(self, err, msg):
        if err is not None:
            logger.error(f"Message delivery failed: {err}")
        else:
            logger.debug(f"Message delivered to {msg.topic()} [{msg.partition()}]")

    async def produce(self, topic: str, key: Optional[str], value: Any):
        loop = asyncio.get_running_loop()
        
        def _produce():
            self.producer.produce(
                topic,
                key=key.encode('utf-8') if key else None,
                value=json.dumps(value).encode('utf-8'),
                callback=self.delivery_report
            )
            # Service delivery reports
            self.producer.poll(0)
            
        await loop.run_in_executor(None, _produce)

    async def flush(self):
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self.producer.flush)


class KafkaConsumerWrapper:
    """Async wrapper for Confluent Kafka Consumer. Handles manual offset commits and retries."""
    def __init__(self, bootstrap_servers: str, group_id: str, topics: List[str]):
        self.conf = {
            'bootstrap.servers': bootstrap_servers,
            'group.id': group_id,
            'auto.offset.reset': 'earliest',
            'enable.auto.commit': False, # Manual commit for idempotency / at-least-once mechanism
            'session.timeout.ms': 10000,
        }
        self.consumer = Consumer(self.conf)
        self.consumer.subscribe(topics)
        self.running = False

    async def consume_loop(self, message_handler: Callable[[str, Any], Awaitable[None]]):
        self.running = True
        loop = asyncio.get_running_loop()
        
        while self.running:
            # Poll synchronously in a separate thread to avoid blocking asyncio event loop
            msg = await loop.run_in_executor(None, self.consumer.poll, 1.0)
            
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    logger.error(f"Consumer error: {msg.error()}")
                    continue

            try:
                key = msg.key().decode('utf-8') if msg.key() else ""
                value = json.loads(msg.value().decode('utf-8')) if msg.value() else {}
                
                # Execute application logic
                await message_handler(key, value)
                
                # Commit explicitly ONLY if processing succeeded (at-least-once delivery)
                await loop.run_in_executor(None, self.consumer.commit, msg, False)
                
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                # Message is NOT committed. Depending on use case, this might infinitely retry.
                # In production, a Dead Letter Queue (DLQ) push would be integrated here.

    def stop(self):
        self.running = False
        self.consumer.close()
