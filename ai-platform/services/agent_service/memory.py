import os
import json
import redis.asyncio as redis
from typing import List, Dict, Any, Optional
from shared.logger.formatter import get_logger

logger = get_logger("redis_memory", "agent_service")

class RedisMemoryManager:
    """Manages conversational memory and session state with TTL."""
    
    def __init__(self, ttl_seconds: int = 3600):
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.ttl_seconds = ttl_seconds

    def _get_key(self, session_id: str) -> str:
        return f"session_memory:{session_id}"

    async def get_history(self, session_id: str) -> List[Dict[str, str]]:
        """Retrieve conversational history. Returns empty list if none exists."""
        key = self._get_key(session_id)
        data = await self.redis_client.get(key)
        if data:
            return json.loads(data)
        return []

    async def add_interaction(self, session_id: str, role: str, content: str):
        """Append a new message to the session history and refresh TTL."""
        key = self._get_key(session_id)
        history = await self.get_history(session_id)
        
        history.append({
            "role": role,
            "content": content
        })
        
        # Save back and reset TTL
        await self.redis_client.setex(key, self.ttl_seconds, json.dumps(history))
        logger.debug(f"Updated memory for session {session_id}. History length: {len(history)}.")

    async def clear_session(self, session_id: str):
        """Clear the memory for a session explicitly."""
        key = self._get_key(session_id)
        await self.redis_client.delete(key)
