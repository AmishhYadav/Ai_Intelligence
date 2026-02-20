import os
import redis.asyncio as redis
from fastapi import Request, HTTPException
from functools import wraps
from shared.logger.formatter import get_logger

logger = get_logger("rate_limit", "api_gateway")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

def rate_limiter(requests_per_minute: int = 60):
    """
    Dependency / Decorator for Redis-backed sliding window rate limiting.
    Rate limits based on Client IP address.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            client_ip = request.client.host if request.client else "unknown"
            endpoint = request.url.path
            
            key = f"rate_limit:{client_ip}:{endpoint}"
            
            try:
                # Basic token bucket / counter approach for simplicity and speed
                current_hits = await redis_client.get(key)
                
                if current_hits is not None and int(current_hits) >= requests_per_minute:
                    raise HTTPException(status_code=429, detail="Too Many Requests")
                
                pipe = redis_client.pipeline()
                pipe.incr(key)
                if current_hits is None:
                    # Set expiry only if key is newly created
                    pipe.expire(key, 60)
                await pipe.execute()
                
            except redis.ConnectionError:
                # Fail open if Redis is down to prevent complete API outage,
                # but log the critical dependency failure.
                logger.error("Redis Connection Error, bypassing rate limit.")
                
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator
