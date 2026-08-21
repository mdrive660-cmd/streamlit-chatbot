import streamlit as st
import google.generativeai as genai
import os
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Vaibhav ka Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize API key from environment variable
api_key = os.getenv("GOOGLE_AI_STUDIO_API_KEY")

if not api_key:
    st.error("⚠️ Google AI Studio API key not found!")
    st.info("Please set the environment variable: `GOOGLE_AI_STUDIO_API_KEY`")
    st.stop()

# Configure the API
genai.configure(api_key=api_key)

# Custom CSS for modern styling
st.markdown("""
    <style>
    .main {
        max-width: 1200px;
        margin: 0 auto;
    }
    .chat-message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0.5rem;
        display: flex;
        gap: 1rem;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    .assistant-message {
        background-color: #f3e5f5;
        border-left: 4px solid #9c27b0;
    }
    .header {
        text-align: center;
        padding: 2rem 0;
        border-bottom: 2px solid #eee;
        margin-bottom: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar configuration
with st.sidebar:
    st.title("⚙️ Settings")
    
    # Model selection
    model_name = st.selectbox(
        "Select Model",
        ["gemini-3.7-flash", "gemini-2.5-flash-lite", "gemini-3.1-flash-lite"],
        help="Choose the AI model to use for responses"
    )
    
    # Temperature slider
    temperature = st.slider(
        "Temperature (Creativity)",
        min_value=0.0,
        max_value=2.0,
        value=0.7,
        step=0.1,
        help="Higher values = more creative, Lower values = more focused"
    )
    
    # Max tokens slider
    max_tokens = st.slider(
        "Max Response Length",
        min_value=100,
        max_value=4096,
        value=2048,
        step=100,
        help="Maximum length of the AI response"
    )
    
    # Clear chat button
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    st.divider()
    st.caption("🚀 Powered by Gen-Z' Brain ")

# Main header
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown("""
        <div class="header">
            <h1>🤖 Vaibhav ka Chatbot</h1>
            <p style="color: #666; margin: 0;">Powered by Gen-Z' Brain</p>
        </div>
    """, unsafe_allow_html=True)

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

if "model" not in st.session_state:
    st.session_state.model = None

# Display chat messages
chat_container = st.container()
with chat_container:
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(f"""
                <div class="chat-message user-message">
                    <div style="flex: 1;">
                        <strong>👤 You</strong>
                        <p style="margin: 0.5rem 0 0 0;">{message['content']}</p>
                        <small style="color: #999;">{message.get('timestamp', '')}</small>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div class="chat-message assistant-message">
                    <div style="flex: 1;">
                        <strong>🤖 Assistant</strong>
                        <p style="margin: 0.5rem 0 0 0;">{message['content']}</p>
                        <small style="color: #999;">{message.get('timestamp', '')}</small>
                    </div>
                </div>
            """, unsafe_allow_html=True)

# Input area
st.divider()
col1, col2 = st.columns([0.9, 0.1])

with col1:
    user_input = st.text_input(
        "Type your message...",
        placeholder="Ask me anything but not personal!",
        label_visibility="collapsed",
        key="user_input"
    )

with col2:
    send_button = st.button("Send", use_container_width=True, type="primary")

# Process user input
if send_button and user_input:
    # Add user message to history
    st.session_state.messages.append({
        "role": "user",
        "content": user_input,
        "timestamp": datetime.now().strftime("%H:%M:%S")
    })
    
    try:
        # Show loading spinner
        with st.spinner("🤔 Sochne de yrrr..."):
            # Initialize the model
            model = genai.GenerativeModel(
                model_name=model_name,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                )
            )
            
            # Get chat history for context
            chat_history = [
                {
                    "role": msg["role"],
                    "parts": msg["content"]
                }
                for msg in st.session_state.messages[:-1]  # Exclude the latest user message
            ]
            
            # Start or continue conversation
            chat = model.start_chat(history=chat_history)
            response = chat.send_message(user_input)
            
            # Add assistant response to history
            st.session_state.messages.append({
                "role": "assistant",
                "content": response.text,
                "timestamp": datetime.now().strftime("%H:%M:%S")
            })
        
        # Rerun to display the new messages
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Kuch toh gadbad hai : {str(e)}")
        # Remove the last user message if there was an error
        st.session_state.messages.pop()

# Footer
st.divider()
st.markdown("""
    <div style="text-align: center; color: #999; padding: 1rem;">
        <small>
            💡 Tip: Adjust the model, temperature, and max length in the sidebar for better results
        </small>
    </div>
""", unsafe_allow_html=True)
