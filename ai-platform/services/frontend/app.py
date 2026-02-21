import streamlit as st
import httpx
import uuid
import datetime
import os
import time
from dotenv import load_dotenv
import jwt

# Load environment variables
load_dotenv()

# --- Configuration & Styling ---
st.set_page_config(
    page_title="Nova",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom highly dynamic CSS for a Soft Tech Editorial aesthetic
st.markdown("""
<style>
    /* Global Base - Deep Charcoal / Soft Tech Editorial */
    html, body, [data-testid="stAppViewContainer"], .stApp {
        background-color: #0d0d12 !important;
        color: #e2e2e8 !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }

    /* Target the top header area */
    header[data-testid="stHeader"] {
        background-color: transparent !important;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
    }

    /* Hide Streamlit default UI noise */
    #MainMenu, footer, .stDeployButton, [data-testid="stToolbar"] {
        visibility: hidden !important;
        display: none !important;
    }

    /* Typography Hierarchy & Contrast */
    h1, h2, h3, h4, h5, h6 {
        color: #f8f8f9 !important;
        font-weight: 600 !important;
    }

    /* AGGRESSIVE WILDCARD OVERRIDE FOR EMOTION CACHE CONTAINERS */
    div[class*="st-emotion-cache"] {
        background-color: transparent !important;
        border-color: rgba(255, 255, 255, 0.05) !important;
    }

    /* Re-apply dark to specific structural containers */
    [data-testid="stSidebar"] {
        background-color: #0b0b0f !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
    }
    
    .stChatMessage {
        background-color: #13131a !important;
        border: 1px solid rgba(255, 255, 255, 0.04) !important;
        border-radius: 8px !important;
        margin-bottom: 0.8rem !important;
    }
    
    [data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #16161f !important;
        border-left: 2px solid #3f3f4e !important;
    }
    
    [data-testid="stChatMessage"]:nth-child(even) {
        background-color: #13131a !important;
        border-left: 2px solid #8b5cf6 !important;
    }

    /* File Uploader Section Styling */
    [data-testid="stFileUploader"] section {
        background-color: #13131a !important;
        border: 1px dashed rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px !important;
    }

    /* Chat Input Fixed Footer Styling */
    [data-testid="stChatInput"] {
        background-color: #0d0d12 !important;
        border-top: 1px solid rgba(255, 255, 255, 0.05) !important;
    }
    
    [data-testid="stChatInput"] textarea {
        background-color: #13131a !important;
        color: #f8f8f9 !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px !important;
    }

    /* Metric Card Styling */
    [data-testid="stMetric"] {
        background-color: #13131a !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 8px !important;
        padding: 10px !important;
    }

    /* Sidebar Navigation Overrides */
    [data-testid="stSidebarNav"] {
        background-color: #0b0b0f !important;
    }

    /* Custom Accent Classes */
    .header-glow {
        display: inline-block;
        padding-bottom: 2px;
        border-bottom: 2px solid transparent;
        border-image: linear-gradient(to right, #8b5cf6, transparent) 1;
    }

    .stButton>button {
        background-color: #1c1c24 !important;
        color: #e2e2e8 !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 4px !important;
    }

    .stButton>button:hover {
        background-color: #252530 !important;
        color: #fff !important;
    }
    
    /* Technical Elements */
    .streamlit-expanderHeader {
        background-color: #13131a !important;
    }
    .streamlit-expanderContent {
        background-color: #0b0b0f !important;
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
if "is_processing" not in st.session_state:
    st.session_state.is_processing = False

# --- Backend Config ---
API_URL = os.getenv("API_URL", "http://localhost:8000/v1")
HEADERS = {"Authorization": f"Bearer {st.session_state.jwt_token}"}

# --- Sidebar UI ---
with st.sidebar:
    st.markdown("<h2 style='margin-bottom:0;'><span class='header-glow'>Nova Core</span></h2>", unsafe_allow_html=True)
    st.markdown("<p class='text-muted' style='margin-top:0;'>Async Intelligence Mesh</p>", unsafe_allow_html=True)
    
    st.markdown("<hr class='subtle-divider'>", unsafe_allow_html=True)
    
    # Telemetry abstractions grouped
    st.markdown("<span style='font-size: 0.75rem; text-transform: uppercase; color: #8b8d98; font-weight: 600; letter-spacing: 0.05em;'>System Status</span>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<div style='margin-top: 0.5rem;'><span class='status-dot'></span><span style='font-size: 0.85rem; color: #e2e2e8;'>Event Bus</span></div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div style='margin-top: 0.5rem;'><span class='status-dot'></span><span style='font-size: 0.85rem; color: #e2e2e8;'>Vector Node</span></div>", unsafe_allow_html=True)
        
    st.markdown("<hr class='subtle-divider'>", unsafe_allow_html=True)
    
    # Data Ingestion Section
    st.markdown("<span style='font-size: 0.75rem; text-transform: uppercase; color: #8b8d98; font-weight: 600; letter-spacing: 0.05em;'>Knowledge Base Ingestion</span>", unsafe_allow_html=True)
    st.markdown("<p class='text-muted'>Push unstructured context to Qdrant.</p>", unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("Upload contextual knowledge", type=["txt", "md"], label_visibility="collapsed")
    
    if uploaded_file is not None:
        if st.button("Vectorize Document", use_container_width=True, type="primary"):
            st.session_state.is_processing = True
            with st.status("Ingesting document parameters...", expanded=True) as status:
                try:
                    content = uploaded_file.getvalue().decode("utf-8")
                    payload = {
                        "raw_text": content,
                        "metadata": {"source": uploaded_file.name, "priority": "high"}
                    }
                    st.write("Extracting content and assembling payload...")
                    time.sleep(0.5) # Perceived responsiveness
                    
                    st.write("Publishing `ingestion_events` to Kafka gateway...")
                    # Fire & Forget to Gateway
                    httpx.post(f"{API_URL}/ingest", json=payload, headers=HEADERS, timeout=10.0)
                    
                    status.update(label="Document queued for vectorization", state="complete", expanded=False)
                except Exception as e:
                    status.update(label=f"Ingestion failed: {e}", state="error")
            st.session_state.is_processing = False
                
    st.markdown("<hr class='subtle-divider'>", unsafe_allow_html=True)
    
    # Session Management
    st.markdown("<span style='font-size: 0.75rem; text-transform: uppercase; color: #8b8d98; font-weight: 600; letter-spacing: 0.05em;'>Session Logic</span>", unsafe_allow_html=True)
    if st.button("Purge Active Memory", use_container_width=True):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.chat_history = []
        st.rerun()
        
    # Technical Footer
    st.markdown("""
        <div style="margin-top: 40px; padding-top: 20px;">
            <div style="padding: 10px 12px; border-radius: 6px; background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05);">
                <span class='text-muted' style="font-family: monospace; font-size: 0.75rem;">
                NODE: gw-eu-west-1<br>
                SESS: %s
                </span>
            </div>
        </div>
    """ % st.session_state.session_id[:8], unsafe_allow_html=True)

# --- Main Layout ---
# Clean title area
st.markdown("<h1><span class='header-glow'>Workspace</span></h1>", unsafe_allow_html=True)
st.markdown("<p class='text-muted' style='margin-bottom: 2rem;'>Interact with the autonomous reasoning mesh. The agent integrates dynamically with your configured MCP tools and semantic context.</p>", unsafe_allow_html=True)

# Render Chat History
for msg in st.session_state.chat_history:
    # Use SVG icons for a cleaner look than emojis
    icon = "✨" if msg["role"] == "assistant" else "👤"
    with st.chat_message(msg["role"], avatar=icon):
        if msg.get("metadata"):
            # If there's technical metadata to display in an expander
            st.markdown(msg["content"])
            with st.expander("View Event Telemetry"):
                st.json(msg["metadata"])
        else:
            st.markdown(msg["content"])

# Chat Input Container
# Floating input field using st.chat_input
if prompt := st.chat_input("Command or query intent... (e.g., 'Analyze anomalous patterns')", disabled=st.session_state.is_processing):
    
    # 1. Add user message
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)
        
    # 2. Process Interaction with structured feedback
    with st.chat_message("assistant", avatar="✨"):
        
        # Progressive UI feedback using experimental block
        with st.status("Initializing reasoning logic...", expanded=True) as status:
            try:
                # Add slight delay for perceived intelligent processing
                st.write("Formulating intent schema...")
                time.sleep(0.3)
                
                payload = {
                    "action": "ui_query",
                    "session_id": st.session_state.session_id,
                    "payload": {"query": prompt}
                }
                
                st.write("Resolving Kafka topic partitions `user_events`...")
                time.sleep(0.3)
                
                response = httpx.post(f"{API_URL}/action", json=payload, headers=HEADERS, timeout=5.0)
                
                if response.status_code in [200, 202]:
                    status.update(label="Event broadcast complete", state="complete", expanded=False)
                    
                    # Clean, professional response formatting
                    reply_content = """**Signal Acknowledged**  
The asynchronous reasoning agent has adopted task `ui_query`.

*Note: In production environments, client instances connect via WebSockets to stream exact inference chunks from the egress node. The current execution is decoupled.*"""
                    
                    st.markdown(reply_content)
                    
                    event_telemetry = {
                        "event_protocol": "Kafka/TCP",
                        "target_topic": "user_events",
                        "session_binding": st.session_state.session_id,
                        "gateway_status": response.status_code,
                        "timestamp_utc": datetime.datetime.utcnow().isoformat()
                    }
                    
                    with st.expander("View Event Telemetry"):
                        st.json(event_telemetry)
                        
                    st.session_state.chat_history.append({
                        "role": "assistant", 
                        "content": reply_content,
                        "metadata": event_telemetry
                    })
                else:
                    status.update(label="System gateway rejected signal", state="error")
                    st.error(f"API Gateway Error code: {response.status_code}")
                    
            except Exception as e:
                status.update(label="Connection interrupted", state="error")
                st.error(f"Network error routing through Gateway: {e}")
