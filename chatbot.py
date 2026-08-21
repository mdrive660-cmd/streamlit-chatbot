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
st.sidebar.info("Enter your Sanity (GROQ) Project ID, Dataset and API token here. You can also store these in Streamlit secrets as `sanity.project_id`, `sanity.dataset`, `sanity.token`.")

# Try to load from secrets as default
default_project = st.secrets.get("sanity", {}).get("project_id") if st.secrets else None
default_dataset = st.secrets.get("sanity", {}).get("dataset") if st.secrets else None
default_token = st.secrets.get("sanity", {}).get("token") if st.secrets else None

project_id = st.sidebar.text_input("Project ID", value=default_project or "")
dataset = st.sidebar.text_input("Dataset", value=default_dataset or "")
api_token = st.sidebar.text_input("API token", value=default_token or "", type="password")

use_groq_direct = st.sidebar.checkbox("Treat user input as full GROQ query", value=False)
max_results = st.sidebar.number_input("Max results", min_value=1, max_value=100, value=5)

if "sanity_configured" not in st.session_state:
    st.session_state.sanity_configured = False

if st.sidebar.button("Save configuration"):
    if project_id and dataset and api_token:
        st.session_state.sanity_configured = True
        st.session_state.project_id = project_id
        st.session_state.dataset = dataset
        st.session_state.api_token = api_token
        st.sidebar.success("Configuration saved to session (not persisted). You can also add these to Streamlit secrets.")
    else:
        st.sidebar.error("Please provide Project ID, Dataset and API token.")

if st.sidebar.button("Test connection"):
    # Quick sanity check by querying for empty query (will return schema info or 400) - we use a safe simple query
    if project_id and dataset and api_token:
        test_q = "*[] | limit(1)"
        try:
            url = f"https://{project_id}.api.sanity.io/v2021-10-21/data/query/{dataset}?query={quote_plus(test_q)}"
            headers = {"Authorization": f"Bearer {api_token}"}
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                st.sidebar.success("Connection successful (Sanity responded). You can now use queries.")
            else:
                st.sidebar.error(f"Connection failed: {r.status_code} {r.text}")
        except Exception as e:
            st.sidebar.error(f"Connection error: {e}")
    else:
        st.sidebar.error("Please provide Project ID, Dataset and API token.")

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
    
    .input-group {
        display: flex;
        gap: 10px;
        align-items: center;
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
def query_groq(groq_query: str, project_id: str, dataset: str, token: str, timeout: int = 10, limit: int = 5):
    """Execute a GROQ query against Sanity and return parsed JSON or raise.

    groq_query: the full GROQ query string
    project_id, dataset, token: Sanity configuration
    limit: used only when templates are applied; caller may include its own limit
    """
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
                st.markdown(f"""
                    <div class="message bot-message">
                        <div class="message-content bot-message-content">
                            {message['content']}
                            <div class="timestamp">{message['timestamp']}</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

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

    # If Sanity config is available either in session_state (saved) or from sidebar inputs, use it
    cfg_project = st.session_state.get("project_id") or project_id
    cfg_dataset = st.session_state.get("dataset") or dataset
    cfg_token = st.session_state.get("api_token") or api_token

    bot_response = "🚀 Coming Soon!\n\nWe're working hard to bring you the best experience. This feature will be available shortly. Stay tuned!"

    if cfg_project and cfg_dataset and cfg_token:
        # Build GROQ query
        try:
            if use_groq_direct:
                groq_q = user_input
            else:
                # A generic search template that attempts to match common fields.
                # Note: Sanity schemas differ by project. If this fails, try enabling "Treat input as full GROQ query" and write a custom query.
                safe_q = user_input.replace('"', "\\\"")
                groq_q = f'*[title match "{safe_q}*" || name match "{safe_q}*" || description match "{safe_q}*" || body match "{safe_q}*"]{{_id, _type, title, name, description, body}}[0...{max_results}]'

            result = query_groq(groq_q, cfg_project, cfg_dataset, cfg_token, limit=max_results)
            # result structure: {"ms":..., "result": [...]}
            hits = result.get("result") if isinstance(result, dict) else None
            if not hits:
                bot_response = "No results found for your query in the Sanity dataset. Try a different query or enable 'Treat input as full GROQ query' and craft a query tailored to your schema."
            else:
                # Pretty format the results
                pretty = []
                for i, h in enumerate(hits, start=1):
                    # Convert to a compact but readable string
                    try:
                        title = h.get("title") or h.get("name") or h.get("_id")
                    except Exception:
                        title = str(h)
                    pretty.append(f"{i}. Type: {h.get('_type', 'unknown')} — {title}\n{json.dumps(h, ensure_ascii=False, indent=2)}")
                bot_response = "\n\n".join(pretty)
        except requests.HTTPError as http_err:
            bot_response = f"Error querying Sanity: {http_err} — Response: {getattr(http_err.response, 'text', '')}"
        except Exception as e:
            bot_response = f"Error querying Sanity: {e}\n\nIf you're unsure about the correct GROQ query for your dataset, enable 'Treat input as full GROQ query' in the sidebar and write a query, or provide your dataset schema."
    else:
        bot_response = "Sanity configuration not found. Please set Project ID, Dataset and API token in the sidebar (or store them in Streamlit secrets)."

    # Add bot response
    timestamp = datetime.now().strftime("%H:%M")
    st.session_state.messages.append({
        "role": "bot",
        "content": bot_response,
        "timestamp": timestamp
    })

    # Rerun to refresh the chat
    st.rerun()
