import asyncio
from fastapi import FastAPI
import uvicorn
from typing import Optional

def start_health_server(service_name: str, port: int = 8080):
    """
    Spawns a background FastAPI server for Kubernetes health/liveness probes 
    for Kafka workers that don't natively expose HTTP.
    """
    app = FastAPI(title=f"{service_name} Health API")
    
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": service_name}
        
    @app.get("/metrics")
    async def metrics():
        return {"service": service_name, "status": "active", "metrics": "not_implemented"}

    config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="warning")
    server = uvicorn.Server(config)
    
    # Attach to the running asyncio loop
    loop = asyncio.get_running_loop()
    loop.create_task(server.serve())
