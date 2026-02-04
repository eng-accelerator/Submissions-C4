streamlit>=1.28.0
requests
import streamlit as st
import json
import os
import requests
import time
from datetime import datetime
from pathlib import Path

# --- 1. CONFIGURATION & SETUP ---
CHAT_DIR = Path("chat_history")
CHAT_DIR.mkdir(exist_ok=True)

st.set_page_config(page_title="Hiring Assistant Chatbot", layout="wide", page_icon="🤖")

# --- 2. HELPER FUNCTIONS (STORAGE & API) ---

def save_chat(chat_id, messages, title):
    file_path = CHAT_DIR / f"{chat_id}.json"
    data = {
        "chat_id": chat_id,
        "title": title,
        "messages": messages,
        "updated_at": datetime.now().isoformat()
    }
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

def get_all_chats():
    chats = []
    for file in CHAT_DIR.glob("*.json"):
        with open(file, "r") as f:
            chats.append(json.load(f))
    return sorted(chats, key=lambda x: x['updated_at'], reverse=True)

def delete_chat(chat_id):
    file_path = CHAT_DIR / f"{chat_id}.json"
    if file_path.exists():
        os.remove(file_path)

def stream_openrouter(messages, api_key):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "openai/gpt-oss-120b", # As per assignment
        "messages": [{"role": m["role"], "content": m["content"]} for m in messages],
        "stream": True
    }
    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data, stream=True)
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8').replace('data: ', '')
                if decoded_line == '[DONE]': break
                try:
                    json_line = json.loads(decoded_line)
                    content = json_line['choices'][0]['delta'].get('content', '')
                    if content: yield content
                except: continue
    except Exception as e:
        yield f"Error: {str(e)}"

# --- 3. SESSION STATE INITIALIZATION ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")
if "chat_title" not in st.session_state:
    st.session_state.chat_title = "New Chat"

# --- 4. SIDEBAR: CONVERSATION MANAGEMENT ---
with st.sidebar:
    st.header("💬 Conversations")
    
    # New Chat Button
    if st.button("➕ New Chat", use_container_width=True):
        st.session_state.current_chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.session_state.messages = []
        st.session_state.chat_title = "New Chat"
        st.rerun()

    st.divider()
    st.subheader("Chat History")
    
    # List Saved Chats
    for chat in get_all_chats():
        col1, col2 = st.columns([0.8, 0.2])
        
        # Select Chat
        is_current = chat['chat_id'] == st.session_state.current_chat_id
        label = f"🟢 {chat['title']}" if is_current else chat['title']
        
        if col1.button(label, key=f"load_{chat['chat_id']}", use_container_width=True):
            st.session_state.current_chat_id = chat['chat_id']
            st.session_state.messages = chat['messages']
            st.session_state.chat_title = chat['title']
            st.rerun()
            
        # Delete Chat
        if col2.button("🗑️", key=f"del_{chat['chat_id']}"):
            delete_chat(chat['chat_id'])
            if is_current:
                st.session_state.messages = []
                st.session_state.chat_title = "New Chat"
            st.rerun()

    st.divider()
    
    # API Key Input (Required for OpenRouter)
    api_key = st.text_input("OpenRouter API Key", type="password")
    if not api_key:
        st.info("Please enter your API Key to start chatting.", icon="🔑")

    st.subheader("Settings")
    st.toggle("Dark mode", value=True)
    if st.button("🗑️ Clear Current Chat", use_container_width=True):
        st.session_state.messages = []
        save_chat(st.session_state.current_chat_id, [], "New Chat")
        st.rerun()

# --- 5. MAIN INTERFACE ---
st.title(f"🤖 {st.session_state.chat_title}")

# Optional Summarizer Expander (Requirement 4)
with st.expander("📝 Summarize Conversation"):
    if st.button("Generate Summary"):
        if st.session_state.messages:
            summary_prompt = st.session_state.messages + [{"role": "user", "content": "Summarize this conversation briefly."}]
            summary = "".join(list(stream_openrouter(summary_prompt, api_key)))
            st.write(summary)
        else:
            st.write("No messages to summarize.")

# Display Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat Input
if prompt := st.chat_input("What would you like to know?"):
    if not api_key:
        st.error("API Key is missing!")
    else:
        # 1. Add User Message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 2. Update Title if it's the first message
        if len(st.session_state.messages) == 1:
            st.session_state.chat_title = prompt[:30] + "..." if len(prompt) > 30 else prompt

        # 3. Generate Assistant Response (Streaming)
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            full_response = ""
            
            for chunk in stream_openrouter(st.session_state.messages, api_key):
                full_response += chunk
                response_placeholder.markdown(full_response + "▌")
            
            response_placeholder.markdown(full_response)
        
        # 4. Save to History
        st.session_state.messages.append({"role": "assistant", "content": full_response})
        save_chat(st.session_state.current_chat_id, st.session_state.messages, st.session_state.chat_title)
