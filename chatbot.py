# ──────────────────────────────────────────────────────────────────────
# app.py
# Streamlit chatbot that can talk to OpenAI or Groq.
# API keys are entered directly in the sidebar (no .env needed).
# ──────────────────────────────────────────────────────────────────────

import streamlit as st

# ----------------------------------------------------------------------
# 1️⃣ Sidebar – enter API keys, choose provider, model, etc.
# ----------------------------------------------------------------------
with st.sidebar:
    st.title("⚙️ Settings")

    # ---- 1️⃣ Paste API keys -------------------------------------------------
    # Keys are kept in `st.session_state` only for the lifetime of the session.
    # They are NOT written to disk.
    if "openai_key" not in st.session_state:
        st.session_state.openai_key = ""
    if "groq_key" not in st.session_state:
        st.session_state.groq_key = ""

    # Text input boxes (type="password" masks the characters)
    st.session_state.openai_key = st.text_input(
        label="OpenAI API key",
        value=st.session_state.openai_key,
        type="password",
        help="Paste your `sk-…` key here. Leave empty if you only want Groq.",
    )

    st.session_state.groq_key = st.text_input(
        label="Groq API key",
        value=st.session_state.groq_key,
        type="password",
        help="Paste your `gsk_…` key here. Leave empty if you only want OpenAI.",
    )

    # ---- 2️⃣ Provider selector ---------------------------------------------
    # Default to whichever key is filled; if both are present let the user choose.
    default_provider = (
        "OpenAI"
        if st.session_state.openai_key
        else ("Groq" if st.session_state.groq_key else "OpenAI")
    )
    provider = st.radio(
        "LLM provider",
        options=["OpenAI", "Groq"],
        index=0 if default_provider == "OpenAI" else 1,
        help="Select which API to call. The appropriate key must be filled.",
    )

    # ---- 3️⃣ Model picker ---------------------------------------------------
    if provider == "OpenAI":
        model = st.selectbox(
            "Model",
            options=["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
            index=0,
            help="OpenAI models – pick one based on cost/quality.",
        )
    else:  # Groq
        model = st.selectbox(
            "Model",
            options=[
                "mixtral-8x7b-32768",
                "gemma-7b-it",
                "llama3-8b-8192",
                "llama3-70b-8192",
            ],
            index=0,
            help="Groq models – see https://groq.com/models.",
        )

    # ---- 4️⃣ Temperature & max‑tokens sliders --------------------------------
    temperature = st.slider(
        "Creativity (temperature)",
        min_value=0.0,
        max_value=1.0,
        value=0.7,
        step=0.05,
        help="Higher = more random, lower = more deterministic.",
    )

    max_tokens = st.number_input(
        "Maximum tokens per reply",
        min_value=256,
        max_value=4096,
        value=1024,
        step=64,
        help="Upper limit on the length of the assistant's response.",
    )

    # ---- 5️⃣ Optional system prompt editor ----------------------------------
    if "system_prompt" not in st.session_state:
        st.session_state.system_prompt = (
            "You are a helpful, friendly assistant. Answer concisely, "
            "ask clarifying questions if needed, and keep the tone conversational."
        )
    edit_prompt = st.checkbox("Edit system prompt", value=False)
    if edit_prompt:
        st.session_state.system_prompt = st.text_area(
            "System prompt",
            value=st.session_state.system_prompt,
            height=120,
        )

    # ---- 6️⃣ Clear conversation button --------------------------------------
    if st.button("🗑️ Clear conversation", use_container_width=True):
        # Reset everything except the system prompt (kept in session_state)
        st.session_state.messages = [
            {"role": "system", "content": st.session_state.system_prompt}
        ]
        st.experimental_rerun()

# ----------------------------------------------------------------------
# 2️⃣ Sanity checks – make sure the selected provider has a key
# ----------------------------------------------------------------------
if provider == "OpenAI" and not st.session_state.openai_key:
    st.error("🚨 OpenAI key is empty. Paste it in the sidebar.")
    st.stop()
if provider == "Groq" and not st.session_state.groq_key:
    st.error("🚨 Groq key is empty. Paste it in the sidebar.")
    st.stop()

# ----------------------------------------------------------------------
# 3️⃣ Helper: talk to the chosen backend
# ----------------------------------------------------------------------
def get_chat_response(messages: list[dict]) -> str:
    """
    Sends the conversation history to the selected provider and returns
    the assistant's reply as plain text.
    """
    if provider == "OpenAI":
        # ---------- OpenAI path ----------
        import openai

        openai.api_key = st.session_state.openai_key
        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content.strip()
        except Exception as exc:
            st.error(f"❗ OpenAI API error: {exc}")
            return "Sorry, I couldn't generate a response."

    else:  # provider == "Groq"
        # ---------- Groq path ----------
        from groq import Groq

        client = Groq(api_key=st.session_state.groq_key)
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            # Groq returns the same structure as OpenAI
            return response.choices[0].message.content.strip()
        except Exception as exc:
            st.error(f"❗ Groq API error: {exc}")
            return "Sorry, I couldn't generate a response."

# ----------------------------------------------------------------------
# 4️⃣ Page header
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="💬 Streamlit Chatbot (OpenAI ↔ Groq)",
    page_icon="💬",
    layout="centered",
    initial_sidebar_state="expanded",
)

st.title("💬 Streamlit Chatbot – OpenAI ↔ Groq")
st.caption(
    "Paste your API key(s) in the sidebar, pick a model, and start chatting!"
)

# ----------------------------------------------------------------------
# 5️⃣ Session state – keep the whole conversation
# ----------------------------------------------------------------------
if "messages" not in st.session_state:
    # Initialise with the (possibly edited) system prompt
    st.session_state.messages = [
        {"role": "system", "content": st.session_state.system_prompt}
    ]

# ----------------------------------------------------------------------
# 6️⃣ Render chat history (skip the system message)
# ----------------------------------------------------------------------
def render_chat():
    for msg in st.session_state.messages[1:]:   # ignore system entry
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.markdown(msg["content"])
        elif msg["role"] == "assistant":
            with st.chat_message("assistant"):
                st.markdown(msg["content"])

render_chat()

# ----------------------------------------------------------------------
# 7️⃣ Text input – the user sends a new message
# ----------------------------------------------------------------------
if user_input := st.chat_input
