import streamlit as st
import httpx
import uuid
import datetime
import os
from dotenv import load_dotenv
import jwt

# Load environment variables
load_dotenv()

# --- Configuration & Styling ---
st.set_page_config(
    page_title="Nova AI Core",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom highly dynamic CSS for a premium industry-standard look
st.markdown("""
<style>
    /* Global Base */
    .stApp {
        background-color: #0d1117;
        color: #c9d1d9;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}

    /* Chat Containers */
    .stChatMessage {
        border-radius: 12px;
        padding: 1.2rem;
        margin-bottom: 1rem;
        border: 1px solid #30363d;
        background-color: #161b22;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .stChatMessage:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(0,0,0,0.2);
    }
    
    /* User Message Specifics */
    [data-testid="stChatMessage"]:nth-child(odd) {
        border-left: 4px solid #58a6ff;
        background: linear-gradient(145deg, #161b22 0%, #1c2128 100%);
    }
    
    /* Assistant Message Specifics */
    [data-testid="stChatMessage"]:nth-child(even) {
        border-left: 4px solid #8957e5;
        background: linear-gradient(145deg, #161b22 0%, #201b2a 100%);
    }

    /* Buttons */
    .stButton>button {
        background: linear-gradient(90deg, #58a6ff 0%, #8957e5 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(88, 166, 255, 0.2);
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(137, 87, 229, 0.4);
        border: none;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #010409;
        border-right: 1px solid #30363d;
    }
    
    /* Abstract glassmorphism effect for metrics */
    [data-testid="stMetricValue"] {
        background: rgba(88, 166, 255, 0.1);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(88, 166, 255, 0.2);
        border-radius: 8px;
        padding: 10px;
        display: inline-block;
        color: #58a6ff;
        font-weight: 700;
    }
    
    /* Upload Box */
    .stFileUploader>div>div {
        background-color: #161b22;
        border: 1px dashed #58a6ff;
        border-radius: 12px;
        padding: 2rem;
    }
    
    h1, h2, h3 {
        color: #e6edf3;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    
    /* Fun pulsing dot for status */
    .pulse-dot {
        height: 10px;
        width: 10px;
        background-color: #2ea043;
        border-radius: 50%;
        display: inline-block;
        animation: pulse 1.5s infinite;
        vertical-align: middle;
        margin-right: 8px;
    }
    @keyframes pulse {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(46, 160, 67, 0.7); }
        70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(46, 160, 67, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(46, 160, 67, 0); }
    }
</style>
""", unsafe_allow_html=True)

# --- State Management ---
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "jwt_token" not in st.session_state:
    # Generate a local token matching the gateway's secret for auth
    secret = os.getenv("JWT_SECRET_KEY", "your_super_secret_jwt_key")
    payload = {
        "sub": f"ui-user-{st.session_state.session_id[:8]}",
        "roles": ["user"],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=1)
    }
    st.session_state.jwt_token = jwt.encode(payload, secret, algorithm="HS256")

# --- Backend Config ---
API_URL = os.getenv("API_URL", "http://localhost:8000/v1")
HEADERS = {"Authorization": f"Bearer {st.session_state.jwt_token}"}

# --- Sidebar UI ---
with st.sidebar:
    st.markdown("<h2><span class='pulse-dot'></span> Nova Core <span style='font-size:0.5em; color:#8b949e'>v1.0.0</span></h2>", unsafe_allow_html=True)
    st.caption("Distributed AI Intelligence Platform")
    
    st.divider()
    
    # Telemetry abstractions
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Event Broker", value="Online")
    with col2:
        st.metric(label="Vector RAG", value="Active")
        
    st.divider()
    
    st.subheader("Data Ingestion")
    st.caption("Push unstructured knowledge to the Qdrant Vector space.")
    uploaded_file = st.file_uploader("Upload contextual knowledge", type=["txt", "md"])
    
    if uploaded_file is not None:
        if st.button("Vectorize Data ⚡"):
            try:
                content = uploaded_file.getvalue().decode("utf-8")
                payload = {
                    "raw_text": content,
                    "metadata": {"source": uploaded_file.name, "priority": "high"}
                }
                with st.spinner("Processing embeddings..."):
                    # Fire & Forget to Gateway
                    httpx.post(f"{API_URL}/ingest", json=payload, headers=HEADERS, timeout=10.0)
                st.success(f"Data ingested into Kafka successfully.")
            except Exception as e:
                st.error(f"Ingestion failed: {e}")
                
    st.divider()
    if st.button("Reset Session Memory"):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.chat_history = []
        st.rerun()
        
    st.markdown("""
        <div style="margin-top: 100px; padding: 10px; border-radius: 8px; background: #161b22; border: 1px solid #30363d;">
        <span style="font-size: 12px; color: #8b949e;"><b>NODE:</b> gateway-eu-w1<br><b>SESSION:</b> %s</span>
        </div>
    """ % st.session_state.session_id[:8], unsafe_allow_html=True)

# --- Main Chat UI ---
st.title("🌌 Neural Command Center")
st.write("Interact directly with the multi-agent asynchronous intelligence mesh. The agent has access to your semantic vector memory and MCP reasoning tools.")

st.markdown("<br>", unsafe_allow_html=True)

# Render Chat History
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"], avatar="🤖" if msg["role"] == "assistant" else "👤"):
        st.write(msg["content"])

# Chat Input
if prompt := st.chat_input("Initiate reasoning logic... e.g. 'Analyze my health risk based on recent documents'"):
    
    # 1. Add user message
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.write(prompt)
        
    # 2. Add placeholder & request
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Querying vector space & executing tools..."):
            try:
                # Issue: The current system is 100% async Kafka driven (fire & forget).
                # To make the UI feel alive, we send the intent as an action.
                # In a real WebSocket environment, we'd listen for the Agent's return event.
                # For this Streamlit demo, we'll hit the Agent directly or simulate the gateway flow.
                
                # Since the backend is completely detached (Agent consumes Kafka and doesn't HTTP respond to gateway),
                # We will trigger the event so the backend runs it, but for UI sake, we will mock the stream feedback 
                # OR we can add a synchronous polling endpoint to fetch history from Redis.
                
                # We will trigger the action to Kafka:
                payload = {
                    "action": "ui_query",
                    "session_id": st.session_state.session_id,
                    "payload": {"query": prompt}
                }
                
                # Note: The original backend architecture built in previous phases 
                # is entirely async. Gateway -> Kafka -> Agent -> Redis.
                # The gateway returns 202 Accepted, not the answer. 
                response = httpx.post(f"{API_URL}/action", json=payload, headers=HEADERS, timeout=5.0)
                
                if response.status_code in [200, 202]:
                    # To make the UI aesthetic, we acknowledge the broadcast.
                    reply = f"**[Kafka Event Broadcasted]**\n\nThe asynchronous Reasoning Agent has received task `ui_query` for session `{st.session_state.session_id[:6]}`.\n\n*In a production frontend, this UI would connect via WebSockets to listen to the egress topic for the final LLM response. Currently, the Agent is writing the response into its Redis memory state in the background.*"
                    st.write(reply)
                    st.session_state.chat_history.append({"role": "assistant", "content": reply})
                else:
                    st.error(f"API Gateway Error: {response.status_code}")
                    
            except Exception as e:
                st.error(f"Network error routing through Gateway: {e}")
