import streamlit as st
from openai import OpenAI
import json
from datetime import datetime
import os

# Set page configuration (must be first Streamlit command)
st.set_page_config(
    page_title="Streamlit Hello",
    page_icon="👋",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Hey who are you? 👋")

# Function to save chat history
def save_chat_history(messages):
    """Save chat history to a JSON file with datetime-based ID"""
    if not messages or len(messages) == 0:
        return  # Don't save empty chats

    # Create chat_history directory if it doesn't exist
    os.makedirs("chat_history", exist_ok=True)

    # Generate chat ID based on current datetime
    chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Get chat title from first user message
    chat_title = "New Chat"
    for msg in messages:
        if msg["role"] == "user":
            chat_title = msg["content"][:50]  # First 50 chars of first user message
            break

    # Create chat data structure
    chat_data = {
        "chat_id": chat_id,
        "chat_title": chat_title,
        "timestamp": datetime.now().isoformat(),
        "conversation": messages
    }

    # Save to JSON file
    filename = f"chat_history/{chat_id}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(chat_data, f, indent=2, ensure_ascii=False)

    return filename

# Function to load chat history from JSON file
def load_chat_history(filename):
    """Load chat history from a JSON file"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            chat_data = json.load(f)
        return chat_data
    except Exception as e:
        st.error(f"Error loading chat: {str(e)}")
        return None

# Function to get all saved chats
def get_saved_chats():
    """Get list of all saved chat files"""
    if not os.path.exists("chat_history"):
        return []

    chat_files = []
    for filename in os.listdir("chat_history"):
        if filename.endswith(".json"):
            filepath = os.path.join("chat_history", filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    chat_data = json.load(f)
                chat_files.append({
                    "filename": filepath,
                    "chat_id": chat_data.get("chat_id", ""),
                    "chat_title": chat_data.get("chat_title", "Untitled"),
                    "timestamp": chat_data.get("timestamp", "")
                })
            except:
                continue

    # Sort by timestamp (newest first)
    chat_files.sort(key=lambda x: x["timestamp"], reverse=True)
    return chat_files

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'current_chat_id' not in st.session_state:
    st.session_state.current_chat_id = None

# Initialize OpenAI client
client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key="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",
  default_headers={
        "HTTP-Referer": "http://localhost:8501",  # Optional: shows on OpenRouter rankings
        "X-Title": "My ChatBot",                  # Optional: shows on OpenRouter rankings
    }
)

# Sidebar
st.sidebar.title("Conversations")

# Button in sidebar to start new conversation
if st.sidebar.button("🆕 New Chat"):
    # Save current chat history before clearing
    if st.session_state.messages:
        saved_file = save_chat_history(st.session_state.messages)
        st.sidebar.success(f"✅ Chat saved!")

    # Clear messages for new chat
    st.session_state.messages = []
    st.session_state.current_chat_id = None
    st.rerun()

# Display chat message count in sidebar
st.sidebar.markdown("---")
st.sidebar.caption(f"💬 {len(st.session_state.messages)} messages in current chat")

# Display chat history in sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("📜 Chat History")

saved_chats = get_saved_chats()

if saved_chats:
    for chat in saved_chats:
        # Create a unique key for each button
        load_button_key = f"load_chat_{chat['chat_id']}"
        delete_button_key = f"delete_chat_{chat['chat_id']}"

        # Show timestamp and title
        chat_display = chat['chat_title']
        timestamp_display = datetime.fromisoformat(chat['timestamp']).strftime("%b %d, %Y %I:%M %p")

        # Create a container for each chat
        with st.sidebar.container():
            col1, col2 = st.sidebar.columns([5, 1])
            with col1:
                if st.button(f"💬 {chat_display}", key=load_button_key, use_container_width=True):
                    # Load this chat
                    chat_data = load_chat_history(chat['filename'])
                    if chat_data:
                        st.session_state.messages = chat_data['conversation']
                        st.session_state.current_chat_id = chat_data['chat_id']
                        st.rerun()
            with col2:
                if st.button("🗑️", key=delete_button_key, help="Delete this chat"):
                    # Delete the chat file
                    try:
                        os.remove(chat['filename'])
                        # If this was the currently loaded chat, clear it
                        if st.session_state.current_chat_id == chat['chat_id']:
                            st.session_state.messages = []
                            st.session_state.current_chat_id = None
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error deleting chat: {str(e)}")
            st.sidebar.caption(f"📅 {timestamp_display}")
            st.sidebar.markdown("---")
else:
    st.sidebar.info("No saved chats yet. Start a conversation!")

# Main page - Display all chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Chat input
if prompt := st.chat_input("Type your message here..."):
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Get AI response
    try:
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = client.chat.completions.create(
                  model="openai/gpt-4o-mini",
                  messages=st.session_state.messages
                )
                assistant_message = response.choices[0].message.content
                st.write(assistant_message)

        # Add assistant message to chat history
        st.session_state.messages.append({"role": "assistant", "content": assistant_message})

    except Exception as e:
        st.error(f"Error: {str(e)}")
