import os
import sys
import asyncio
import httpx
from typing import Any
import google.generativeai as genai
from google.generativeai.types import content_types

# Add root to python path for shared modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from shared.kafka.client import KafkaConsumerWrapper, KafkaProducerWrapper
from shared.schemas.events import ReasoningTask, AlertEvent
from shared.logger.formatter import get_logger
from services.agent_service.memory import RedisMemoryManager

logger = get_logger("agent_service_main", "agent_service")

KAFKA_BROKER = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
REASONING_TOPIC = os.getenv("KAFKA_REASONING_TASKS_TOPIC", "reasoning_tasks")
ALERTS_TOPIC = os.getenv("KAFKA_ALERTS_TOPIC", "alerts")
RETRIEVAL_API_URL = os.getenv("RETRIEVAL_API_URL", "http://localhost:8001/v1/search")
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8002/tools/execute")

# Setup Gemini Config
genai.configure(api_key=os.getenv("GEMINI_API_KEY", "dummy_key_for_testing"))
model = genai.GenerativeModel('gemini-1.5-flash')

producer = KafkaProducerWrapper(bootstrap_servers=KAFKA_BROKER, client_id="agent-producer")
consumer = KafkaConsumerWrapper(bootstrap_servers=KAFKA_BROKER, group_id="agent-group", topics=[REASONING_TOPIC])
memory_manager = RedisMemoryManager()

# --- MCP Tool Python Wrappers for Gemini ---
def analyze_health_risk(user_id: str, vitals_summary: str) -> dict:
    """Analyzes physiological or behavioral data to calculate a health risk probability."""
    with httpx.Client() as client:
        res = client.post(MCP_SERVER_URL, json={"tool_name": "analyze_health_risk", "arguments": {"user_id": user_id, "vitals_summary": vitals_summary}})
        return res.json()

def detect_pattern_anomaly(user_id: str, context: str) -> dict:
    """Scans recent log activity for the user to detect anomalous workflow patterns."""
    with httpx.Client() as client:
        res = client.post(MCP_SERVER_URL, json={"tool_name": "detect_pattern_anomaly", "arguments": {"user_id": user_id, "context": context}})
        return res.json()

def summarize_recent_activity(session_id: str) -> dict:
    """Fetches a high-level summary of the user's recent interactions."""
    with httpx.Client() as client:
        res = client.post(MCP_SERVER_URL, json={"tool_name": "summarize_recent_activity", "arguments": {"session_id": session_id}})
        return res.json()

# Register functions with the model
tools = [analyze_health_risk, detect_pattern_anomaly, summarize_recent_activity]
agent_model = genai.GenerativeModel('gemini-1.5-flash', tools=tools)

async def fetch_retrieval_context(query: str) -> str:
    """Queries the internal Retrieval Service."""
    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(RETRIEVAL_API_URL, json={"query": query, "limit": 3})
            res.raise_for_status()
            results = res.json().get("results", [])
            return "\\n".join([f"Context: {r['payload'].get('text_content', '')}" for r in results])
        except Exception as e:
            logger.error(f"Retrieval error: {e}")
            return "No additional context available."

async def process_reasoning_task(key: str, value: Any):
    try:
        task = ReasoningTask(**value)
        logger.info(f"Processing ReasoningTask for session {task.session_id}")
        
        # 1. Fetch History
        history = await memory_manager.get_history(task.session_id)
        
        # 2. Fetch Context (RAG)
        context_str = ""
        if task.context_keys or "analyze" in task.query.lower():
            context_str = await fetch_retrieval_context(task.query)
            
        # 3. Build Prompt
        system_instruction = "You are a senior AI reasoning agent. You have access to tools via MCP. Use them if necessary based on user queries or context. If you encounter critical risks, explicitly state 'ESCALATION REQUIRED'."
        
        prompt = f"{system_instruction}\\n\\nRelevant RAG Context:\\n{context_str}\\n\\nUser Query: {task.query}"
        
        # Reconstruct Gemini chat history
        # (Converting simplified dict history back into Gemini types)
        gemini_history = []
        for msg in history:
            gemini_history.append({"role": msg["role"], "parts": [msg["content"]]})
            
        chat = agent_model.start_chat(history=gemini_history)
        
        # 4. Generate response (Tool Calling happens automatically via SDK if configured, or manually if we intercept)
        # Using enable_automatic_function_calling=True makes the Python SDK execute our functions
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(None, lambda: chat.send_message(prompt))
        
        final_answer = response.text
        logger.info(f"Agent response: {final_answer[:100]}...")
        
        # 5. Save to memory
        await memory_manager.add_interaction(task.session_id, "user", task.query)
        await memory_manager.add_interaction(task.session_id, "model", final_answer)
        
        # 6. Dispatch Alerts if escalation detected
        if "ESCALATION REQUIRED" in final_answer or "HIGH" in final_answer:
            alert = AlertEvent(
                source="agent_service",
                severity="CRITICAL",
                message=f"Agent escalated task for user {task.user_id}",
                context={"session_id": task.session_id, "agent_response": final_answer}
            )
            await producer.produce(ALERTS_TOPIC, key=task.session_id, value=alert.model_dump(mode='json'))
            logger.warning(f"Escalation Alert dispatched for session {task.session_id}")

    except Exception as e:
        logger.error(f"Failed to process reasoning task: {e}", exc_info=True)
        raise e

async def main():
    logger.info("Starting Reasoning Agent Service...")
    try:
        await consumer.consume_loop(process_reasoning_task)
    except KeyboardInterrupt:
        logger.info("Shutting down Agent Service...")
    finally:
        consumer.stop()
        await producer.flush()

if __name__ == "__main__":
    asyncio.run(main())
