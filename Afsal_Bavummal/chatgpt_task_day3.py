"""
ChatGPT-Style Web App using Streamlit and OpenRouter API
=========================================================
"""

import streamlit as st
import requests
import json
import os
import uuid
from datetime import datetime
from pathlib import Path

# =============================================================================
# CONFIGURATION
# =============================================================================
OPENROUTER_API_KEY = "key"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
MODEL_NAME = "openai/gpt-oss-120b"
CHATS_DIRECTORY = "chats_data"

# =============================================================================
# CUSTOM CSS FOR TWO-WAY CHAT LAYOUT
# =============================================================================
def inject_chat_css():
    st.markdown("""
    <style>
    /* User messages on the right */
    [data-testid="stChatMessage"][data-testid-role="user"] {
        flex-direction: row-reverse;
        text-align: right;
    }
    
    [data-testid="stChatMessage"][data-testid-role="user"] > div:first-child {
        margin-left: 12px;
        margin-right: 0;
    }
    
    /* Alternative selector for user messages */
    .stChatMessage:has([data-testid="chatAvatarIcon-user"]) {
        flex-direction: row-reverse;
    }
    
    .stChatMessage:has([data-testid="chatAvatarIcon-user"]) > div:first-child {
        margin-left: 12px;
        margin-right: 0;
    }
    
    /* Style user bubble */
    .stChatMessage:has([data-testid="chatAvatarIcon-user"]) [data-testid="stMarkdownContainer"] {
        background-color: #e74c3c;
        color: white;
        padding: 10px 15px;
        border-radius: 15px 15px 5px 15px;
    }
    
    /* Style assistant bubble */
    .stChatMessage:has([data-testid="chatAvatarIcon-assistant"]) [data-testid="stMarkdownContainer"] {
        background-color: #2d2d2d;
        color: #e0e0e0;
        padding: 10px 15px;
        border-radius: 15px 15px 15px 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def ensure_chats_directory():
    Path(CHATS_DIRECTORY).mkdir(parents=True, exist_ok=True)

def generate_chat_filename(chat_id: str, start_time: str) -> str:
    time_formatted = start_time.replace(':', '-').replace(' ', '_')
    return f"{chat_id}_{time_formatted}.json"

def get_chat_filepath(chat_id: str) -> str:
    ensure_chats_directory()
    for filename in os.listdir(CHATS_DIRECTORY):
        if filename.startswith(chat_id) and filename.endswith('.json'):
            return os.path.join(CHATS_DIRECTORY, filename)
    return None

def load_all_chats() -> dict:
    ensure_chats_directory()
    chats = {}
    for filename in os.listdir(CHATS_DIRECTORY):
        if filename.endswith('.json'):
            filepath = os.path.join(CHATS_DIRECTORY, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    chat_data = json.load(f)
                    chats[chat_data['id']] = chat_data
            except Exception:
                continue
    return chats

def save_chat_to_disk(chat_data: dict):
    ensure_chats_directory()
    old_filepath = get_chat_filepath(chat_data['id'])
    if old_filepath and os.path.exists(old_filepath):
        os.remove(old_filepath)
    
    filename = generate_chat_filename(chat_data['id'], chat_data['start_time'])
    filepath = os.path.join(CHATS_DIRECTORY, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(chat_data, f, indent=2, ensure_ascii=False)

def delete_chat_from_disk(chat_id: str):
    filepath = get_chat_filepath(chat_id)
    if filepath and os.path.exists(filepath):
        os.remove(filepath)

def create_new_chat() -> dict:
    chat_id = str(uuid.uuid4())[:8]
    start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    chat_data = {
        "id": chat_id,
        "title": "New Chat",
        "start_time": start_time,
        "messages": [],
        "summary": ""
    }
    save_chat_to_disk(chat_data)
    return chat_data

def delete_chat(chat_id: str):
    if chat_id in st.session_state.chats:
        del st.session_state.chats[chat_id]
    delete_chat_from_disk(chat_id)
    if st.session_state.chats:
        st.session_state.current_chat_id = list(st.session_state.chats.keys())[0]
    else:
        new_chat = create_new_chat()
        st.session_state.chats[new_chat['id']] = new_chat
        st.session_state.current_chat_id = new_chat['id']

def clear_chat(chat_id: str):
    if chat_id in st.session_state.chats:
        st.session_state.chats[chat_id]['messages'] = []
        st.session_state.chats[chat_id]['summary'] = ""
        st.session_state.chats[chat_id]['title'] = "New Chat"
        save_chat_to_disk(st.session_state.chats[chat_id])

def call_model(messages: list, system_prompt: str = None) -> tuple:
    if "OPENROUTER_API_KEY_HERE" in OPENROUTER_API_KEY:
        return None, "API key not configured."
    
    api_messages = []
    if system_prompt:
        api_messages.append({"role": "system", "content": system_prompt})
    else:
        api_messages.append({"role": "system", "content": "You are a helpful assistant."})
    
    api_messages.extend(messages)
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8501",
        "X-Title": "ChatGPT Clone"
    }
    
    payload = {
        "model": MODEL_NAME,
        "messages": api_messages,
        "temperature": 0.7,
        "max_tokens": 4096
    }
    
    try:
        response = requests.post(
            f"{OPENROUTER_BASE_URL}/chat/completions",
            headers=headers,
            json=payload,
            timeout=120
        )
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content'], None
        else:
            return None, f"API Error ({response.status_code})"
    except Exception as e:
        return None, f"Error: {str(e)}"

def generate_chat_summary(messages: list) -> tuple:
    if not messages:
        return None, "No messages."
    conversation_text = "\n".join([f"{msg['role'].upper()}: {msg['content']}" for msg in messages])
    summary_messages = [{"role": "user", "content": f"Summarize concisely:\n\n{conversation_text}"}]
    return call_model(summary_messages, "You are a summary assistant.")

def initialize_session_state():
    if 'chats' not in st.session_state:
        st.session_state.chats = load_all_chats()
        if not st.session_state.chats:
            new_chat = create_new_chat()
            st.session_state.chats[new_chat['id']] = new_chat
    
    if 'current_chat_id' not in st.session_state:
        if st.session_state.chats:
            st.session_state.current_chat_id = list(st.session_state.chats.keys())[0]
        else:
            new_chat = create_new_chat()
            st.session_state.chats[new_chat['id']] = new_chat
            st.session_state.current_chat_id = new_chat['id']
    
    if 'is_thinking' not in st.session_state:
        st.session_state.is_thinking = False
    
    if 'pending_prompt' not in st.session_state:
        st.session_state.pending_prompt = None

# =============================================================================
# UI COMPONENTS
# =============================================================================

def render_sidebar():
    with st.sidebar:
        st.header("Conversations")
        
        if st.button("+ New Chat", type="primary", use_container_width=True):
            new_chat = create_new_chat()
            st.session_state.chats[new_chat['id']] = new_chat
            st.session_state.current_chat_id = new_chat['id']
            st.rerun()
        
        st.subheader("Chat History")
        
        sorted_chats = sorted(st.session_state.chats.items(), key=lambda x: x[1].get('start_time', ''), reverse=True)
        for chat_id, chat_data in sorted_chats:
            display_title = chat_data['title'][:30] + "..." if len(chat_data['title']) > 30 else chat_data['title']
            
            col1, col2 = st.columns([5, 1])
            with col1:
                if st.button(display_title, key=f"chat_{chat_id}", use_container_width=True):
                    st.session_state.current_chat_id = chat_id
                    st.rerun()
            with col2:
                if st.button("X", key=f"del_{chat_id}"):
                    delete_chat(chat_id)
                    st.rerun()
        
        st.divider()
        st.subheader("Settings")
        
        if st.button("Clear Current Chat", use_container_width=True):
            if st.session_state.current_chat_id:
                clear_chat(st.session_state.current_chat_id)
                st.rerun()

def render_chat_area():
    current_chat = st.session_state.chats.get(st.session_state.current_chat_id)
    if not current_chat:
        return
    
    # Title
    st.title(current_chat['title'])
    
    # Summary expander
    with st.expander("Summarize Conversation", expanded=False):
        if current_chat.get('summary'):
            st.write("**Current Summary:**")
            st.write(current_chat['summary'])
            st.divider()
        
        if len(current_chat['messages']) == 0:
            st.info("No messages to summarize yet.")
        else:
            if st.button("Generate Summary"):
                with st.spinner("Summarizing..."):
                    summary, error = generate_chat_summary(current_chat['messages'])
                    if summary:
                        current_chat['summary'] = summary
                        save_chat_to_disk(current_chat)
                        st.rerun()
                    elif error:
                        st.error(error)
    
    st.divider()
    
    # Messages
    if current_chat['messages']:
        for msg in current_chat['messages']:
            with st.chat_message(msg['role']):
                st.write(msg['content'])
    else:
        st.info("Start a conversation by typing a message below!")
    
    # Thinking indicator
    if st.session_state.is_thinking:
        with st.chat_message("assistant"):
            st.write("Thinking...")
        
        if st.session_state.pending_prompt:
            messages = [{"role": m['role'], "content": m['content']} for m in current_chat['messages']]
            response, error = call_model(messages)
            
            if response:
                current_chat['messages'].append({"role": "assistant", "content": response})
            else:
                current_chat['messages'].append({"role": "assistant", "content": f"Error: {error}"})
            
            save_chat_to_disk(current_chat)
            st.session_state.is_thinking = False
            st.session_state.pending_prompt = None
            st.rerun()
    
    # Chat input
    if not st.session_state.is_thinking:
        prompt = st.chat_input("Message ChatGPT Clone...")
        if prompt:
            current_chat['messages'].append({"role": "user", "content": prompt})
            
            if len(current_chat['messages']) == 1:
                current_chat['title'] = prompt[:40] + ("..." if len(prompt) > 40 else "")
            
            save_chat_to_disk(current_chat)
            st.session_state.is_thinking = True
            st.session_state.pending_prompt = prompt
            st.rerun()

def main():
    st.set_page_config(
        page_title="ChatGPT Clone",
        page_icon="💬",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    initialize_session_state()
    inject_chat_css()
    render_sidebar()
    render_chat_area()

if __name__ == "__main__":
    main()
