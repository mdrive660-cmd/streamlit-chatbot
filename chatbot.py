import os
import time
import streamlit as st
from groq import Groq
from typing import List, Dict


# ---------- Helpers ----------

def truncate_to_50_words(text: str) -> str:
    words = text.split()
    if len(words) <= 50:
        return text
    return " ".join(words[:50]) + " ... (truncated to 50 words)"


def prepare_messages(messages: List[Dict], max_messages: int = 12, max_chars: int = 3000) -> List[Dict]:
    """
    Keep the system message and the last `max_messages` chat messages.
    If the combined characters still exceed `max_chars`, drop older messages until under the limit.
    This reduces the request size to avoid 413 Request Entity Too Large errors.
    """
    if not messages:
        return messages

    # Always keep the first system message (if present and role == system)
    system_msg = None
    rest = []
    if messages[0].get("role") == "system":
        system_msg = messages[0]
        rest = messages[1:]
    else:
        rest = messages[:]

    # Take the last max_messages messages from rest
    kept = rest[-max_messages:]

    candidate = [system_msg] + kept if system_msg else kept

    # If still too large, drop oldest kept messages until under limit
    total_chars = sum(len(m.get("content", "")) for m in candidate if m)
    while total_chars > max_chars and (len(kept) > 1):
        # drop the oldest of kept (front)
        kept = kept[1:]
        candidate = [system_msg] + kept if system_msg else kept
        total_chars = sum(len(m.get("content", "")) for m in candidate if m)

    # If everything still too large, keep only the last user message plus system
    if total_chars > max_chars:
        # find last user or assistant message
        last = rest[-1]
        candidate = [system_msg, last] if system_msg else [last]

    # Remove any None entries
    candidate = [m for m in candidate if m]
    return candidate


# ---------- Streamlit UI ----------

st.set_page_config(page_title="Streamlit Groq Chatbot", page_icon="🤖", layout="wide")

# Minimal modern CSS for cleaner chat bubbles
st.markdown(
    """
    <style>
    .chat-container {max-width:900px;margin:0 auto;padding:12px}
    .stApp {background: linear-gradient(180deg,#0f172a 0%, #071033 100%); color: #e6eef8}
    .chat-box {background: rgba(255,255,255,0.03); padding:16px; border-radius:12px}
    .msg-user {background: linear-gradient(90deg,#2563eb,#7c3aed); color:white; padding:10px 14px; border-radius:12px; display:inline-block}
    .msg-assistant {background: rgba(255,255,255,0.06); color:#e6eef8; padding:10px 14px; border-radius:12px; display:inline-block}
    .meta {font-size:12px; color:#9fb0d9}
    .title {font-weight:700; font-size:26px}
    .sidebar .stButton>button {background:#2563eb; color:white}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="chat-container">', unsafe_allow_html=True)
col1, col2 = st.columns([3, 1])

with col1:
    st.markdown('<div class="title">Streamlit Groq Chatbot</div>', unsafe_allow_html=True)
    st.markdown('<div class="meta">Concise answers — at most 50 words. Context trimmed automatically to avoid large requests.</div>', unsafe_allow_html=True)
    st.write("")

with col2:
    st.sidebar.title("Settings")
    api_key = st.sidebar.text_input("GROQ API Key", type="password", value=os.environ.get("GROQ_API_KEY", ""))
    model = st.sidebar.selectbox("Model", ["openai/gpt-oss-120b"], index=0)
    max_context_messages = st.sidebar.slider("Max context messages", min_value=2, max_value=24, value=12)
    max_context_chars = st.sidebar.slider("Max context characters", min_value=1000, max_value=12000, value=3000, step=500)
    if st.sidebar.button("Clear conversation"):
        st.session_state.messages = [
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant. Answer concisely and directly. "
                    "All replies MUST be at most 50 words. Do not add extra commentary or examples."
                ),
            }
        ]
        st.experimental_rerun()

# Require API key
if not api_key:
    st.warning("Enter your GROQ API key in the sidebar or set GROQ_API_KEY environment variable.")
    st.stop()

# Initialize client
client = Groq(api_key=api_key)

# Initialize conversation
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful assistant. Answer concisely and directly. "
                "All replies MUST be at most 50 words. Do not add extra commentary or examples."
            ),
        }
    ]

# Chat input
with st.form("chat_form", clear_on_submit=True):
    user_input = st.text_input("Message", placeholder="Ask a question...")
    submitted = st.form_submit_button("Send")

# Show chat history in a scrollable box
chat_box = st.container()
with chat_box:
    st.markdown('<div class="chat-box">', unsafe_allow_html=True)
    for i, msg in enumerate(st.session_state.messages[1:], start=1):
        role = msg.get("role")
        content = msg.get("content")
        timestamp = msg.get("ts") if msg.get("ts") else ""
        if role == "user":
            st.markdown(f"<div style='text-align:right'><div class='msg-user'>{st.markdown.__self__ and ''}{st.markdown.__self__ if False else ''}{st.markdown.__self__}</div><div class='meta'>{timestamp}</div></div>", unsafe_allow_html=True)
            # user bubble
            st.markdown(f"<div style='text-align:right;margin-bottom:8px'><div class='msg-user'>{st.markdown.__self__ and ''}{content}</div><div class='meta'>{timestamp}</div></div>", unsafe_allow_html=True)
        else:
            # assistant bubble
            st.markdown(f"<div style='text-align:left;margin-bottom:8px'><div class='msg-assistant'>{content}</div><div class='meta'>{timestamp}</div></div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Handle submission
if submitted and user_input:
    # add user message with timestamp
    st.session_state.messages.append({"role": "user", "content": user_input, "ts": time.strftime("%Y-%m-%d %H:%M:%S")})

    # Prepare messages for sending (prune to avoid huge requests)
    messages_to_send = prepare_messages(st.session_state.messages, max_messages=max_context_messages, max_chars=max_context_chars)

    try:
        response = client.chat.completions.create(
            messages=messages_to_send,
            model=model,
        )
        assistant_text = response.choices[0].message.content
        assistant_text = truncate_to_50_words(assistant_text)
        st.session_state.messages.append({"role": "assistant", "content": assistant_text, "ts": time.strftime("%Y-%m-%d %H:%M:%S")})
    except Exception as e:
        err_str = str(e)
        # Rough detection for 413 / request too large
        if "413" in err_str or "request_too_large" in err_str or "Request Entity Too Large" in err_str:
            # Retry with very aggressive trimming (keep only last 2 messages)
            messages_to_send = prepare_messages(st.session_state.messages, max_messages=2, max_chars=1200)
            try:
                response = client.chat.completions.create(
                    messages=messages_to_send,
                    model=model,
                )
                assistant_text = response.choices[0].message.content
                assistant_text = truncate_to_50_words(assistant_text)
                st.session_state.messages.append({"role": "assistant", "content": assistant_text, "ts": time.strftime("%Y-%m-%d %H:%M:%S")})
                st.warning("Context was trimmed to fit the API's size limits.")
            except Exception as e2:
                st.error(f"API error after trimming context: {e2}")
        else:
            st.error(f"API error: {e}")

    # rerun so UI updates and input is cleared
    st.rerun()

# Footer / tips
st.markdown("---")
st.markdown("Tips: use the sidebar sliders to control how much context is sent to the API. If you hit large-request errors, reduce Max context messages or Max context characters.")

st.markdown('</div>', unsafe_allow_html=True)
