import streamlit as st
from datetime import datetime
import requests
import json
from urllib.parse import quote_plus

# Set page configuration
st.set_page_config(
    page_title="Vaibhav Ka App",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Sidebar: GROQ / Sanity configuration
st.sidebar.header("GROQ / Sanity configuration")
st.sidebar.info("Enter your Sanity (GROQ) Project ID and Dataset here. Paste your API token into the 'Session API key' field and click 'Add my API key' to keep it session-only.")

# Try to load from secrets as default
default_project = st.secrets.get("sanity", {}).get("project_id") if st.secrets else None
default_dataset = st.secrets.get("sanity", {}).get("dataset") if st.secrets else None

project_id = st.sidebar.text_input("Project ID", value=default_project or "")
dataset = st.sidebar.text_input("Dataset", value=default_dataset or "")

# Session-only API key input (will not be persisted/shared)
session_api_input = st.sidebar.text_input("Session API key (paste here)", value="", type="password")
if st.sidebar.button("Add my API key (session-only)"):
    if session_api_input:
        # Store only in this user's session state
        st.session_state.session_api_token = session_api_input
        st.sidebar.success("Session API key added for this session only.")
    else:
        st.sidebar.error("Please paste an API key before clicking the button.")

# Show whether a session key is present (masked)
if st.session_state.get("session_api_token"):
    st.sidebar.markdown("**Session API key:** `••••••••••••`  (stored in this browser session only)")
else:
    st.sidebar.info("No session API key set. Paste your key above and click 'Add my API key (session-only)'.")

# Convenience options
use_groq_direct = st.sidebar.checkbox("Treat user input as full GROQ query", value=False)
max_results = st.sidebar.number_input("Max results", min_value=1, max_value=100, value=5)

# Custom CSS for modern UI
st.markdown("""
    <style>
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    
    body {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 0 !important;
    }
    
    .chat-container {
        display: flex;
        flex-direction: column;
        height: 100vh;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    .chat-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        text-align: center;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        border-bottom: 3px solid rgba(255, 255, 255, 0.1);
    }
    
    .chat-header h1 {
        margin: 0;
        font-size: 28px;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    
    .chat-header p {
        margin: 5px 0 0 0;
        font-size: 12px;
        opacity: 0.8;
    }
    
    .messages-container {
        flex: 1;
        overflow-y: auto;
        padding: 20px;
        background: linear-gradient(to bottom, rgba(255, 255, 255, 0.95), rgba(245, 247, 250, 0.95));
    }
    
    .message {
        display: flex;
        margin-bottom: 15px;
        animation: slideIn 0.3s ease-out;
    }
    
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .user-message {
        justify-content: flex-end;
    }
    
    .bot-message {
        justify-content: flex-start;
    }
    
    .message-content {
        max-width: 70%;
        padding: 12px 16px;
        border-radius: 15px;
        font-size: 14px;
        line-height: 1.5;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        white-space: pre-wrap;
    }
    
    .user-message-content {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 15px 15px 0 15px;
    }
    
    .bot-message-content {
        background: white;
        color: #333;
        border-radius: 15px 15px 15px 0;
        border-left: 4px solid #667eea;
    }
    
    .timestamp {
        font-size: 11px;
        opacity: 0.6;
        margin-top: 5px;
    }
    
    .input-container {
        background: white;
        padding: 20px;
        border-top: 1px solid rgba(0, 0, 0, 0.1);
        box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.05);
    }
    
    input[type="text"] {
        flex: 1;
        padding: 12px 16px;
        border: 2px solid #e0e0e0;
        border-radius: 25px;
        font-size: 14px;
        transition: border-color 0.3s;
    }
    
    input[type="text"]:focus {
        outline: none;
        border-color: #667eea;
    }
    
    button {
        padding: 12px 24px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        cursor: pointer;
        font-weight: 600;
        transition: transform 0.2s, box-shadow 0.2s;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
    
    button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(102, 126, 234, 0.6);
    }
    
    button:active {
        transform: translateY(0);
    }
    
    .welcome-message {
        text-align: center;
        color: #667eea;
        padding: 40px 20px;
    }
    
    .welcome-message h2 {
        font-size: 24px;
        margin-bottom: 10px;
    }
    
    .welcome-message p {
        font-size: 14px;
        opacity: 0.7;
    }
    
    /* Scrollbar styling */
    .messages-container::-webkit-scrollbar {
        width: 8px;
    }
    
    .messages-container::-webkit-scrollbar-track {
        background: rgba(0, 0, 0, 0.1);
        border-radius: 10px;
    }
    
    .messages-container::-webkit-scrollbar-thumb {
        background: #667eea;
        border-radius: 10px;
    }
    
    .messages-container::-webkit-scrollbar-thumb:hover {
        background: #764ba2;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Convenience: function to call Sanity GROQ API
def query_groq(groq_query: str, project_id: str, dataset: str, token: str, timeout: int = 10):
    """Execute a GROQ query against Sanity and return parsed JSON or raise."""
    if not (project_id and dataset and token):
        raise ValueError("Missing Sanity configuration (project_id, dataset, or token)")

    encoded = quote_plus(groq_query)
    url = f"https://{project_id}.api.sanity.io/v2021-10-21/data/query/{dataset}?query={encoded}"
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(url, headers=headers, timeout=timeout)
    r.raise_for_status()
    return r.json()

# Chat Header
st.markdown("""
    <div class="chat-header">
        <h1>💬 Vaibhav Ka App</h1>
        <p>Always here to help you</p>
    </div>
""", unsafe_allow_html=True)

# Messages Container
with st.container():
    st.markdown('<div class="messages-container">', unsafe_allow_html=True)
    
    if len(st.session_state.messages) == 0:
        st.markdown("""
            <div class="welcome-message">
                <h2>Welcome to Vaibhav Ka App! 👋</h2>
                <p>Start a conversation by typing your question below</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        for message in st.session_state.messages:
            if message["role"] == "user":
                st.markdown(f"""
                    <div class="message user-message">
                        <div class="message-content user-message-content">
                            {message['content']}
                            <div class="timestamp">{message['timestamp']}</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            else:
                # Bot messages may contain short summaries already; long JSON details are shown in the expander below
                st.markdown(f"""
                    <div class="message bot-message">
                        <div class="message-content bot-message-content">
                            {message['content']}
                            <div class="timestamp">{message['timestamp']}</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# If last query results exist, show a collapsible detailed view (not saved to messages)
if st.session_state.get("last_query_results"):
    with st.expander("Show last query results (detailed JSON)"):
        st.json(st.session_state.get("last_query_results"))

# Input Container
st.markdown('<div class="input-container">', unsafe_allow_html=True)

col1, col2 = st.columns([0.9, 0.1])

with col1:
    user_input = st.text_input(
        "Type your message...",
        placeholder="Ask me anything...",
        label_visibility="collapsed"
    )

with col2:
    send_button = st.button("Send", use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)

# Handle user input
if send_button and user_input.strip():
    # Add user message
    timestamp = datetime.now().strftime("%H:%M")
    st.session_state.messages.append({
        "role": "user",
        "content": user_input,
        "timestamp": timestamp
    })

    # Prefer session-only API token if provided
    cfg_project = project_id
    cfg_dataset = dataset
    cfg_token = st.session_state.get("session_api_token")  # session-only token

    bot_response = "Searching..."

    if cfg_project and cfg_dataset and cfg_token:
        try:
            if use_groq_direct:
                groq_q = user_input
            else:
                safe_q = user_input.replace('"', "\\\"")
                groq_q = f'*[title match "{safe_q}*" || name match "{safe_q}*" || description match "{safe_q}*" || body match "{safe_q}*"]{{_id, _type, title, name, description, body}}[0...{max_results}]'

            result = query_groq(groq_q, cfg_project, cfg_dataset, cfg_token)
            hits = result.get("result") if isinstance(result, dict) else None

            if not hits:
                bot_response = "No results found for your query in the Sanity dataset. Try a different query or enable 'Treat user input as full GROQ query' and craft a query tailored to your schema."
                st.session_state.last_query_results = None
            else:
                # Build a concise human-readable summary for the chat
                lines = []
                for i, h in enumerate(hits, start=1):
                    title = h.get("title") or h.get("name") or h.get("_id")
                    type_name = h.get("_type", "unknown")
                    # pick a short excerpt
                    excerpt = None
                    for field in ("description", "body"):
                        v = h.get(field)
                        if isinstance(v, str) and v.strip():
                            excerpt = v.strip()
                            break
                    if excerpt:
                        # truncate to ~150 chars
                        excerpt = (excerpt[:150] + "…") if len(excerpt) > 150 else excerpt
                        lines.append(f"{i}. [{type_name}] {title} — {excerpt}")
                    else:
                        lines.append(f"{i}. [{type_name}] {title}")

                bot_response = "\n\n".join(lines)
                # store full hits for the expander (per session only)
                st.session_state.last_query_results = hits
        except requests.HTTPError as http_err:
            # avoid exposing token in error messages
            status = getattr(http_err.response, 'status_code', None)
            text = getattr(http_err.response, 'text', '')
            bot_response = f"Error querying Sanity: {status}. Check your project ID, dataset and session API key."
            st.session_state.last_query_results = None
        except Exception as e:
            bot_response = f"Error querying Sanity: {e}\n\nIf unsure about the correct GROQ query, enable 'Treat user input as full GROQ query' and provide a query for your schema."
            st.session_state.last_query_results = None
    else:
        bot_response = "Sanity configuration or session API key not found. Make sure Project ID, Dataset are set in the sidebar and you have added your session API key."
        st.session_state.last_query_results = None

    # Add bot response
    timestamp = datetime.now().strftime("%H:%M")
    st.session_state.messages.append({
        "role": "bot",
        "content": bot_response,
        "timestamp": timestamp
    })

    # Rerun to refresh the chat and show results expander
    st.rerun()
