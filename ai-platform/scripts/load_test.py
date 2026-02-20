import asyncio
import httpx
import time
import uuid

API_URL = "http://localhost:8000"
# Create a dummy JWT for the gateway - Note: Requires valid secret or disabled auth in dev
DUMMY_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyLTEyMyIsInJvbGVzIjpbInVzZXIiXX0.dummy_sig"

async def simulate_ingestion(client: httpx.AsyncClient, i: int):
    payload = {
        "raw_text": f"This is clinical note document number {i}. The patient exhibits normal vitals but irregular sleep patterns.",
        "metadata": {"doc_type": "clinical_note", "priority": "normal"}
    }
    
    headers = {"Authorization": f"Bearer {DUMMY_TOKEN}"}
    response = await client.post(f"{API_URL}/v1/ingest", json=payload, headers=headers)
    return response.status_code

async def simulate_action(client: httpx.AsyncClient, i: int, session_id: str):
    payload = {
        "action": "query_health",
        "session_id": session_id,
        "payload": {
            "query": f"Analyze my health risk based on recent documents. Iteration {i}"
        }
    }
    headers = {"Authorization": f"Bearer {DUMMY_TOKEN}"}
    response = await client.post(f"{API_URL}/v1/action", json=payload, headers=headers)
    return response.status_code

async def main():
    print("Starting Load Test Simulation for AI Platform...")
    session_id = str(uuid.uuid4())
    
    start_time = time.time()
    
    async with httpx.AsyncClient() as client:
        # Simulate 50 parallel document ingestions
        print("Simulating 50 parallel ingestion events...")
        ingest_tasks = [simulate_ingestion(client, i) for i in range(50)]
        ingest_results = await asyncio.gather(*ingest_tasks, return_exceptions=True)
        
        print(f"Ingestion Results: {ingest_results[:5]} (showing first 5)")
        
        # Simulate 20 rapid user actions
        print("Simulating 20 parallel reasoning actions...")
        action_tasks = [simulate_action(client, i, session_id) for i in range(20)]
        action_results = await asyncio.gather(*action_tasks, return_exceptions=True)
        
        print(f"Action Results: {action_results[:5]} (showing first 5)")
        
    duration = time.time() - start_time
    print(f"Load test completed in {duration:.2f} seconds.")

if __name__ == "__main__":
    asyncio.run(main())
