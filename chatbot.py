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


def estimate_tokens_from_text(text: str) -> int:
    """Rough token estimate: assume ~4 characters per token (approximation).
    This is not exact but helps bound request sizes without extra deps.
    """
    return max(1, len(text) // 4)


def prepare_messages_by_token_budget(messages: List[Dict], max_tokens: int = 2000, max_messages: int = 24) -> List[Dict]:
    """
    Keep the system message and then the most recent messages while staying under max_tokens (approx).
    Also cap the number of messages to max_messages.
    This reduces the request size (and likelihood of 413 errors) more accurately than a raw char-count.
    """
    if not messages:
        return messages

    system_msg = messages[0] if messages[0].get("role") == "system" else None
    rest = messages[1:] if system_msg else messages[:]

    # Start from the end (most recent) and add messages until token budget used
    kept = []
    tokens_used = 0
    # Always account for system message tokens
    if system_msg:
        tokens_used += estimate_tokens_from_text(system_msg.get("content", ""))

    # iterate reversed rest
    for m in reversed(rest):
        t = estimate_tokens_from_text(m.get("content", ""))
        if (tokens_used + t) > max_tokens:
            break
        kept.append(m)
        tokens_used += t
        if len(kept) >= max_messages:
            break

    # kept currently reversed (newest first), reverse to original order
    kept = list(reversed(kept))

    candidate = [system_msg] + kept if system_msg else kept
    # Ensure no Nones
    candidate = [m for m in candidate if m]
    # If candidate empty fallback to last message only
    if not candidate and rest:
        candidate = [rest[-1]]
    return candidate


# ---------- Streamlit UI ----------

st.set_page_config(page_title="Modern Streamlit AI Chatbot", page_icon="🤖", layout="wide")

# CSS for a modern UI
st.markdown(
    """
    <style>
    .chat-container {max-width:1000px;margin:12px auto;padding:16px}
    .stApp {background: linear-gradient(180deg,#07122a 0%, #05102a 100%); color: #e6eef8}
    .chat-box {background: rgba(255,255,255,0.02); padding:18px; border-radius:14px}
    .msg-user {background: linear-gradient(90deg,#0ea5e9,#7c3aed); color:white; padding:10px 14px; border-radius:14px; display:inline-block}
    .msg-assistant {background: rgba(255,255,255,0.04); color:#e6eef8; padding:10px 14px; border-radius:14px; display:inline-block}
    .meta {font-size:12px; color:#9fb0d9}
    .title {font-weight:700; font-size:28px}
    .subtitle {color:#9fb0d9}
    .sidebar .stButton>button {background:#2563eb; color:white}
    .small {font-size:12px;color:#9fb0d9}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="chat-container">', unsafe_allow_html=True)
col_main, col_side = st.columns([3, 1])

with col_main:
    st.markdown('<div class="title">Modern Streamlit AI Chatbot</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Concise AI answers — maximum 50 words. Context is auto-trimmed to avoid large requests.</div>', unsafe_allow_html=True)
    st.write("")

with col_side:
    st.sidebar.title("Settings & Controls")
    api_key = st.sidebar.text_input("GROQ API Key (or set GROQ_API_KEY)", type="password", value=os.environ.get("GROQ_API_KEY", ""))
    model = st.sidebar.selectbox("Model", ["groq/compound", "openai/gpt-oss-120b"], index=0)
    token_budget = st.sidebar.slider("Max tokens to send (approx)", min_value=200, max_value=4000, value=1500, step=100)
    max_messages_keep = st.sidebar.slider("Max messages to keep", min_value=1, max_value=48, value=24)
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
    user_input = st.text_area("You", value="", placeholder="Ask me anything... (hit Send)", height=70)
    submitted = st.form_submit_button("Send")

# Display conversation using modern chat components when available
chat_container = st.container()
with chat_container:
    st.markdown('<div class="chat-box">', unsafe_allow_html=True)
    for msg in st.session_state.messages[1:]:
        role = msg.get("role")
        content = msg.get("content")
        ts = msg.get("ts", "")
        if role == "user":
            # user bubble right-aligned
            try:
                st.chat_message("user").write(content)
            except Exception:
                st.markdown(f"<div style='text-align:right;margin-bottom:8px'><div class='msg-user'>{content}</div><div class='meta'>{ts}</div></div>", unsafe_allow_html=True)
        else:
            try:
                st.chat_message("assistant").write(content)
            except Exception:
                st.markdown(f"<div style='text-align:left;margin-bottom:8px'><div class='msg-assistant'>{content}</div><div class='meta'>{ts}</div></div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Handle submission
if submitted and user_input:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_input, "ts": time.strftime("%Y-%m-%d %H:%M:%S")})

    # Prepare messages with token budget
    messages_to_send = prepare_messages_by_token_budget(st.session_state.messages, max_tokens=token_budget, max_messages=max_messages_keep)

    try:
        response = client.chat.completions.create(messages=messages_to_send, model=model)
        assistant_text = response.choices[0].message.content
        assistant_text = truncate_to_50_words(assistant_text)
        st.session_state.messages.append({"role": "assistant", "content": assistant_text, "ts": time.strftime("%Y-%m-%d %H:%M:%S")})
    except Exception as e:
        err = str(e)
        # Detect request-too-large; try aggressive trimming and retry once
        if "413" in err or "request_too_large" in err or "Request Entity Too Large" in err:
            # aggressive trim: only last user message + system, small token budget
            messages_to_send = prepare_messages_by_token_budget(st.session_state.messages, max_tokens=800, max_messages=2)
            try:
                response = client.chat.completions.create(messages=messages_to_send, model=model)
                assistant_text = response.choices[0].message.content
                assistant_text = truncate_to_50_words(assistant_text)
                st.session_state.messages.append({"role": "assistant", "content": assistant_text, "ts": time.strftime("%Y-%m-%d %H:%M:%S")})
                st.warning("Context was trimmed to fit the API size limits.")
            except Exception as e2:
                st.error(f"API error after trimming context: {e2}")
        else:
            st.error(f"API error: {e}")

    # Rerun to refresh UI and clear form
    st.experimental_rerun()

# Footer / tips
st.markdown("---")
st.markdown("<div class='small'>Tips: Use the sidebar to control token budget and number of messages kept. If you keep hitting size errors, lower the token budget or clear history.</div>", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
