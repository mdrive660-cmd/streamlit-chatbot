import os
import time
import streamlit as st
from groq import Groq
from typing import List, Dict


# ---------- Configuration ----------

st.set_page_config(
    page_title="AI Chatbot - Gemini Style",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------- Helpers ----------

def estimate_tokens_from_text(text: str) -> int:
    """Rough token estimate: assume ~4 characters per token."""
    return max(1, len(text) // 4)


def prepare_messages_by_token_budget(
    messages: List[Dict], 
    max_tokens: int = 2000, 
    max_messages: int = 24
) -> List[Dict]:
    """
    Keep the system message and most recent messages within token budget.
    Helps prevent 413 request entity too large errors.
    """
    if not messages:
        return messages

    system_msg = messages[0] if messages and messages[0].get("role") == "system" else None
    rest = messages[1:] if system_msg else messages[:]

    kept = []
    tokens_used = 0
    
    if system_msg:
        tokens_used += estimate_tokens_from_text(system_msg.get("content", ""))

    for m in reversed(rest):
        t = estimate_tokens_from_text(m.get("content", ""))
        if (tokens_used + t) > max_tokens:
            break
        kept.append(m)
        tokens_used += t
        if len(kept) >= max_messages:
            break

    kept = list(reversed(kept))
    candidate = [system_msg] + kept if system_msg else kept
    candidate = [m for m in candidate if m]
    
    if not candidate and rest:
        candidate = [rest[-1]]
    
    return candidate


# ---------- Modern Gemini-Style CSS ----------

st.markdown(
    """
    <style>
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    
    html, body, [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 50%, #0f1629 100%);
        color: #e3e8ef;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
    }
    
    [data-testid="stAppViewContainer"] {
        min-height: 100vh;
    }
    
    .main {
        max-width: 900px;
        margin: 0 auto;
        padding: 0;
        display: flex;
        flex-direction: column;
        height: 100vh;
    }
    
    .chat-header {
        text-align: center;
        padding: 24px 16px 16px;
        background: rgba(10, 14, 39, 0.95);
        border-bottom: 1px solid rgba(227, 232, 239, 0.1);
    }
    
    .chat-header-title {
        font-size: 32px;
        font-weight: 700;
        background: linear-gradient(135deg, #60a5fa, #a78bfa, #f472b6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 4px;
    }
    
    .chat-header-subtitle {
        font-size: 13px;
        color: #a0aec0;
        font-weight: 400;
    }
    
    .chat-messages-container {
        flex: 1;
        overflow-y: auto;
        padding: 20px 16px;
        display: flex;
        flex-direction: column;
        gap: 16px;
        scroll-behavior: smooth;
    }
    
    .chat-messages-container::-webkit-scrollbar {
        width: 6px;
    }
    
    .chat-messages-container::-webkit-scrollbar-track {
        background: transparent;
    }
    
    .chat-messages-container::-webkit-scrollbar-thumb {
        background: rgba(160, 174, 192, 0.3);
        border-radius: 3px;
    }
    
    .chat-messages-container::-webkit-scrollbar-thumb:hover {
        background: rgba(160, 174, 192, 0.5);
    }
    
    .message-wrapper {
        display: flex;
        margin-bottom: 8px;
        animation: fadeIn 0.3s ease-in;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(8px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .message-wrapper.user {
        justify-content: flex-end;
    }
    
    .message-wrapper.assistant {
        justify-content: flex-start;
    }
    
    .message-content {
        padding: 12px 16px;
        border-radius: 16px;
        max-width: 70%;
        word-wrap: break-word;
        line-height: 1.5;
        font-size: 14px;
    }
    
    .message-content.user {
        background: linear-gradient(135deg, #3b82f6, #8b5cf6);
        color: white;
        border-bottom-right-radius: 4px;
    }
    
    .message-content.assistant {
        background: rgba(255, 255, 255, 0.08);
        color: #e3e8ef;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-bottom-left-radius: 4px;
    }
    
    .message-time {
        font-size: 11px;
        color: #64748b;
        margin-top: 4px;
        padding: 0 12px;
    }
    
    .input-container {
        padding: 16px;
        background: rgba(10, 14, 39, 0.95);
        border-top: 1px solid rgba(227, 232, 239, 0.1);
        display: flex;
        gap: 8px;
        align-items: flex-end;
    }
    
    .input-field {
        flex: 1;
        background: rgba(255, 255, 255, 0.08) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        color: #e3e8ef !important;
        border-radius: 12px !important;
        padding: 12px 16px !important;
        font-size: 14px !important;
        transition: all 0.2s ease;
    }
    
    .input-field:focus {
        background: rgba(255, 255, 255, 0.12) !important;
        border: 1px solid rgba(59, 130, 246, 0.5) !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
    }
    
    .send-button {
        background: linear-gradient(135deg, #3b82f6, #8b5cf6) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 10px 20px !important;
        font-weight: 600 !important;
        cursor: pointer !important;
        transition: all 0.2s ease !important;
        height: 42px;
    }
    
    .send-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 16px rgba(59, 130, 246, 0.3) !important;
    }
    
    .send-button:active {
        transform: translateY(0);
    }
    
    .settings-sidebar {
        background: rgba(26, 31, 58, 0.9);
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 16px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .settings-title {
        font-size: 14px;
        font-weight: 600;
        color: #e3e8ef;
        margin-bottom: 12px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .stTextInput > div > div > input {
        color: #e3e8ef !important;
    }
    
    .stSelectbox > div > div {
        background: rgba(255, 255, 255, 0.08) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 8px !important;
        color: #e3e8ef !important;
    }
    
    .stSlider > div > div > div {
        color: #3b82f6 !important;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #ef4444, #f97316) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        width: 100% !important;
        transition: all 0.2s ease !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 16px rgba(239, 68, 68, 0.3) !important;
    }
    
    .empty-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 100%;
        color: #a0aec0;
        text-align: center;
        padding: 40px 20px;
    }
    
    .empty-state-icon {
        font-size: 64px;
        margin-bottom: 16px;
        opacity: 0.6;
    }
    
    .empty-state-title {
        font-size: 24px;
        font-weight: 600;
        color: #e3e8ef;
        margin-bottom: 8px;
    }
    
    .empty-state-subtitle {
        font-size: 14px;
        color: #a0aec0;
        max-width: 300px;
    }
    
    .error-message {
        background: rgba(239, 68, 68, 0.1) !important;
        border: 1px solid rgba(239, 68, 68, 0.3) !important;
        color: #fca5a5 !important;
        border-radius: 8px !important;
        padding: 12px 16px !important;
    }
    
    .success-message {
        background: rgba(34, 197, 94, 0.1) !important;
        border: 1px solid rgba(34, 197, 94, 0.3) !important;
        color: #86efac !important;
        border-radius: 8px !important;
        padding: 12px 16px !important;
    }
    
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Session State Initialization ----------

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful, creative, and intelligent AI assistant. "
                "Provide clear, concise, and accurate answers. "
                "Be friendly and engaging while maintaining professionalism."
            ),
        }
    ]

if "api_key_valid" not in st.session_state:
    st.session_state.api_key_valid = False

# ---------- Layout Structure ----------

# Sidebar Settings
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    
    api_key = st.text_input(
        "GROQ API Key",
        type="password",
        value=os.environ.get("GROQ_API_KEY", ""),
        help="Enter your GROQ API key or set GROQ_API_KEY environment variable"
    )
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        model = st.selectbox(
            "Model",
            ["mixtral-8x7b-32768", "llama2-70b-4096", "gemma-7b-it"],
            index=0,
            help="Select the AI model to use"
        )
    
    with col2:
        token_budget = st.slider(
            "Token Budget",
            min_value=500,
            max_value=4000,
            value=2000,
            step=100,
            help="Maximum tokens to send in request"
        )
    
    max_messages_keep = st.slider(
        "Max Messages",
        min_value=1,
        max_value=50,
        value=24,
        help="Maximum conversation history to keep"
    )
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = [
                {
                    "role": "system",
                    "content": (
                        "You are a helpful, creative, and intelligent AI assistant. "
                        "Provide clear, concise, and accurate answers. "
                        "Be friendly and engaging while maintaining professionalism."
                    ),
                }
            ]
            st.success("Chat cleared!")
            time.sleep(1)
            st.rerun()
    
    with col2:
        if st.button("🔄 New Chat", use_container_width=True):
            st.session_state.messages = [
                {
                    "role": "system",
                    "content": (
                        "You are a helpful, creative, and intelligent AI assistant. "
                        "Provide clear, concise, and accurate answers. "
                        "Be friendly and engaging while maintaining professionalism."
                    ),
                }
            ]
            st.rerun()

# ---------- Main Chat Area ----------

# Header
st.markdown(
    """
    <div class="chat-header">
        <div class="chat-header-title">✨ AI Chatbot</div>
        <div class="chat-header-subtitle">Powered by GROQ • Always here to help</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Check API Key
if not api_key:
    st.markdown(
        """
        <div class="empty-state">
            <div class="empty-state-icon">🔑</div>
            <div class="empty-state-title">API Key Required</div>
            <div class="empty-state-subtitle">
                Please enter your GROQ API key in the sidebar to get started.
                <br><br>
                <a href="https://console.groq.com" target="_blank" style="color: #3b82f6;">Get your API key →</a>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

# Messages Display Container
st.markdown('<div class="chat-messages-container">', unsafe_allow_html=True)

if len(st.session_state.messages) == 1:
    # Empty state
    st.markdown(
        """
        <div class="empty-state">
            <div class="empty-state-icon">👋</div>
            <div class="empty-state-title">What's on your mind?</div>
            <div class="empty-state-subtitle">Start a conversation by typing a message below</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    # Display messages
    for msg in st.session_state.messages[1:]:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        ts = msg.get("ts", "")
        
        role_class = role.lower()
        
        st.markdown(
            f"""
            <div class="message-wrapper {role_class}">
                <div>
                    <div class="message-content {role_class}">{content}</div>
                    <div class="message-time">{ts}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown('</div>', unsafe_allow_html=True)

# ---------- Input Form ----------

st.markdown('<div class="input-container">', unsafe_allow_html=True)

with st.form("chat_input_form", clear_on_submit=True):
    col_input, col_button = st.columns([5, 1])
    
    with col_input:
        user_input = st.text_area(
            "Message",
            value="",
            placeholder="Type your message here... (Shift+Enter for new line)",
            height=44,
            label_visibility="collapsed",
            key="user_message_input",
        )
    
    with col_button:
        submitted = st.form_submit_button(
            "Send",
            use_container_width=True,
            type="primary",
        )

st.markdown('</div>', unsafe_allow_html=True)

# ---------- Handle Message Submission ----------

if submitted and user_input:
    # Add user message
    st.session_state.messages.append({
        "role": "user",
        "content": user_input,
        "ts": time.strftime("%H:%M"),
    })
    
    # Prepare messages for API
    messages_to_send = prepare_messages_by_token_budget(
        st.session_state.messages,
        max_tokens=token_budget,
        max_messages=max_messages_keep
    )
    
    try:
        # Initialize Groq client
        client = Groq(api_key=api_key)
        
        # Make API request with streaming
        with st.spinner("🤔 Thinking..."):
            response = client.chat.completions.create(
                messages=messages_to_send,
                model=model,
                temperature=0.7,
                max_tokens=1000,
            )
            
            assistant_text = response.choices[0].message.content
            
            # Add assistant response
            st.session_state.messages.append({
                "role": "assistant",
                "content": assistant_text,
                "ts": time.strftime("%H:%M"),
            })
    
    except Exception as e:
        err = str(e)
        
        # Handle request too large errors
        if "413" in err or "request_too_large" in err or "Request Entity Too Large" in err:
            # Retry with aggressive trimming
            messages_to_send = prepare_messages_by_token_budget(
                st.session_state.messages,
                max_tokens=800,
                max_messages=2
            )
            
            try:
                client = Groq(api_key=api_key)
                response = client.chat.completions.create(
                    messages=messages_to_send,
                    model=model,
                    temperature=0.7,
                    max_tokens=1000,
                )
                
                assistant_text = response.choices[0].message.content
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": assistant_text,
                    "ts": time.strftime("%H:%M"),
                })
                
                st.warning("⚠️ Context was trimmed due to size limits. Consider clearing old messages.")
            except Exception as e2:
                st.error(f"❌ API Error (after trimming): {e2}")
        else:
            st.error(f"❌ API Error: {e}")
    
    # Rerun to update UI
    st.rerun()

# Footer
st.markdown(
    """
    <div style="text-align: center; padding: 20px; color: #64748b; font-size: 12px; border-top: 1px solid rgba(255, 255, 255, 0.1); margin-top: 20px;">
        <p>💡 Tip: Adjust settings in the sidebar to control token budget and conversation history</p>
        <p style="margin-top: 8px; font-size: 11px;">Powered by <strong>GROQ</strong> • Built with <strong>Streamlit</strong></p>
    </div>
    """,
    unsafe_allow_html=True,
)
