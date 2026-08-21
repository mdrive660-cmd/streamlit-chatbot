import os
import streamlit as st
from groq import Groq


def truncate_to_50_words(text: str) -> str:
    words = text.split()
    if len(words) <= 50:
        return text
    return " ".join(words[:50]) + " ... (truncated to 50 words)"


st.set_page_config(page_title="Streamlit Groq Chatbot", page_icon="🤖")

st.title("Streamlit Groq Chatbot (<= 50 words)")

# API key: prefer sidebar entry, fallback to environment variable
api_key = st.sidebar.text_input(
    "GROQ API Key (or set GROQ_API_KEY env var)",
    type="password",
    value=os.environ.get("GROQ_API_KEY", ""),
)

model = st.sidebar.selectbox("Model", ["groq/compound"], index=0)

if not api_key:
    st.sidebar.warning("Enter your GROQ API key to use the chatbot.")
    st.stop()

# Initialize client
client = Groq(api_key=api_key)

# Session state for conversation
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

# Conversation UI
with st.form("chat_form", clear_on_submit=True):
    user_input = st.text_input("You:", "")
    submitted = st.form_submit_button("Send")

if submitted and user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    try:
        response = client.chat.completions.create(
            messages=st.session_state.messages,
            model=model,
        )
        assistant_text = response.choices[0].message.content
        # Safety: enforce 50-word maximum
        assistant_text = truncate_to_50_words(assistant_text)
        st.session_state.messages.append({"role": "assistant", "content": assistant_text})
    except Exception as e:
        st.error(f"API error: {e}")

# Display conversation
for msg in st.session_state.messages:
    role = msg.get("role")
    content = msg.get("content")
    if role == "system":
        continue
    try:
        if role == "user":
            st.chat_message("user").write(content)
        else:
            st.chat_message("assistant").write(content)
    except Exception:
        # Fallback if st.chat_message isn't available
        st.markdown(f"**{role.title()}:** {content}")

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
