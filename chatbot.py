import streamlit as st
from datetime import datetime

# Set page configuration
st.set_page_config(
    page_title="Vaibhav Ka App",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

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
    
    # Add bot response
    bot_response = "🚀 Coming Soon!\n\nWe're working hard to bring you the best experience. This feature will be available shortly. Stay tuned!"
    timestamp = datetime.now().strftime("%H:%M")
    st.session_state.messages.append({
        "role": "bot",
        "content": bot_response,
        "timestamp": timestamp
    })
    
    # Rerun to refresh the chat
    st.rerun()
