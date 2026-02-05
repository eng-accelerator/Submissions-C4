import streamlit as st
import json
import os
import uuid
import glob
from datetime import datetime
from openai import OpenAI

# --- Configuration & Setup ---
ST_PAGE_TITLE = "Chat Clone"
HISTORY_DIR = "chat_sessions"
# NOTE: Replace with your actual OpenRouter Key
OPENROUTER_API_KEY = "" 
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
MODEL_NAME = "openai/gpt-oss-120b"

st.set_page_config(page_title=ST_PAGE_TITLE, layout="wide", page_icon="💬")

client = OpenAI(
    base_url=OPENROUTER_BASE_URL,
    api_key=OPENROUTER_API_KEY,
)

# --- Storage Management ---

def ensure_history_dir():
    if not os.path.exists(HISTORY_DIR):
        os.makedirs(HISTORY_DIR)

def load_all_chats():
    ensure_history_dir()
    history = {}
    files = glob.glob(os.path.join(HISTORY_DIR, "*.json"))
    for file_path in files:
        try:
            with open(file_path, "r") as f:
                chat_data = json.load(f)
                chat_id = chat_data.get("id", os.path.splitext(os.path.basename(file_path))[0])
                history[chat_id] = chat_data
        except (json.JSONDecodeError, IOError):
            continue 
    return history

def save_chat_to_file(chat_id, chat_data):
    ensure_history_dir()
    file_path = os.path.join(HISTORY_DIR, f"{chat_id}.json")
    chat_data["id"] = chat_id
    with open(file_path, "w") as f:
        json.dump(chat_data, f, indent=4)

def delete_chat_file(chat_id):
    file_path = os.path.join(HISTORY_DIR, f"{chat_id}.json")
    if os.path.exists(file_path):
        os.remove(file_path)

# --- Session State ---

if "history" not in st.session_state:
    st.session_state.history = load_all_chats()

if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None

# --- Helper Functions ---

def create_new_chat():
    new_id = str(uuid.uuid4())
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_chat_data = {
        "id": new_id,
        "title": "New Chat",
        "created_at": timestamp,
        "messages": [],
        "summary": None
    }
    st.session_state.history[new_id] = new_chat_data
    st.session_state.current_chat_id = new_id
    save_chat_to_file(new_id, new_chat_data)

def delete_chat(chat_id):
    if chat_id in st.session_state.history:
        del st.session_state.history[chat_id]
        delete_chat_file(chat_id)
        if st.session_state.current_chat_id == chat_id:
            st.session_state.current_chat_id = None

def clear_current_chat():
    if st.session_state.current_chat_id:
        chat_id = st.session_state.current_chat_id
        st.session_state.history[chat_id]["messages"] = []
        save_chat_to_file(chat_id, st.session_state.history[chat_id])

def generate_summary(chat_id):
    chat_data = st.session_state.history.get(chat_id)
    if not chat_data or not chat_data["messages"]:
        return "No content to summarize."
    
    conversation_text = "\n".join([f"{m['role']}: {m['content']}" for m in chat_data['messages']])
    
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "Summarize the following conversation briefly in 1-2 sentences. Return ONLY the summary."},
                {"role": "user", "content": conversation_text}
            ],
        )
        summary = response.choices[0].message.content
        
        # Create a short title from the summary (first 5 words)
        new_title = " ".join(summary.split()[:5])
        if len(new_title) > 30: new_title = new_title[:30] + "..."
        
        # Update ONLY the specific chat ID
        st.session_state.history[chat_id]["summary"] = summary
        st.session_state.history[chat_id]["title"] = new_title
        
        save_chat_to_file(chat_id, st.session_state.history[chat_id])
        return summary
    except Exception as e:
        return f"Error: {str(e)}"

# --- UI Layout ---

# 1. SIDEBAR
with st.sidebar:
    st.title("Conversations")
    
    if st.button("➕ New Chat", use_container_width=True, type="primary"):
        create_new_chat()
        st.rerun()

    st.markdown("---")
    st.subheader("History")

    sorted_chats = sorted(
        st.session_state.history.items(), 
        key=lambda item: item[1]['created_at'], 
        reverse=True
    )

    for chat_id, chat_data in sorted_chats:
        col1, col2 = st.columns([0.85, 0.15])
        with col1:
            btn_label = chat_data.get("title", "New Chat")
            is_active = (chat_id == st.session_state.current_chat_id)
            # Unique Key for selection button
            if st.button(btn_label, key=f"sel_{chat_id}", use_container_width=True, type="secondary" if not is_active else "primary"):
                st.session_state.current_chat_id = chat_id
                st.rerun()
        with col2:
            # Unique Key for delete button
            if st.button("🗑️", key=f"del_{chat_id}"):
                delete_chat(chat_id)
                st.rerun()

    st.markdown("---")
    if st.button("🧹 Clear Current Chat", use_container_width=True):
        clear_current_chat()
        st.rerun()

# 2. MAIN AREA
if not st.session_state.current_chat_id:
    if not st.session_state.history:
        create_new_chat()
        st.rerun()
    else:
        st.session_state.current_chat_id = sorted_chats[0][0]
        st.rerun()

current_id = st.session_state.current_chat_id
if current_id not in st.session_state.history:
    st.session_state.current_chat_id = None
    st.rerun()

current_chat = st.session_state.history[current_id]

st.title("🤖 " + current_chat.get("title", "Chat"))

# --- BONUS: Summary Expander ---
with st.expander("📝 Summarize Conversation"):
    # CRITICAL FIX: Added unique key based on chat_id
    if st.button("Generate Summary", key=f"gen_sum_{current_id}"):
        with st.spinner("Summarizing..."):
            summary_text = generate_summary(current_id)
            st.rerun() # Rerun to update the title immediately
            
    # Display summary if it exists for THIS chat
    if current_chat.get("summary"):
        st.info(current_chat["summary"])

# Messages
for msg in current_chat["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        st.caption(f"_{msg.get('timestamp', '')}_")

# Input
# CRITICAL FIX: Added unique key to chat input so text doesn't persist across chats
if prompt := st.chat_input("What would you like to know?", key=f"input_{current_id}"):
    timestamp = datetime.now().strftime("%H:%M")
    
    # 1. User Message
    new_msg = {"role": "user", "content": prompt, "timestamp": timestamp}
    st.session_state.history[current_id]["messages"].append(new_msg)
    
    with st.chat_message("user"):
        st.markdown(prompt)
        st.caption(f"_{timestamp}_")

    # 2. Assistant Response
    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": m["role"], "content": m["content"]} for m in current_chat["messages"]],
            stream=True,
        )
        response = st.write_stream(stream)
        
        timestamp = datetime.now().strftime("%H:%M")
        asst_msg = {"role": "assistant", "content": response, "timestamp": timestamp}
        st.session_state.history[current_id]["messages"].append(asst_msg)
    
    # 3. Save
    save_chat_to_file(current_id, st.session_state.history[current_id])

    # Auto-summarize check (only triggers if title is still default)
    if current_chat["title"] == "New Chat" and len(current_chat["messages"]) >= 2:
        generate_summary(current_id)
        st.rerun()