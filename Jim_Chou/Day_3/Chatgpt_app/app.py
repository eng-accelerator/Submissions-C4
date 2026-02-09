#
# Author:  Jim Chou
# Date: 2026-02-05
#
import streamlit as st
import requests
import json
import os
from datetime import datetime
import uuid

# ==========================
# CONFIG
# ==========================
st.set_page_config(
    page_title="ChatGPT Clone",
    page_icon="💬",
    layout="wide"
)

try:
    api_key = st.secrets["OPENROUTER_API_KEY"]
    if (api_key is None or api_key == ""):
        raise ValueError
except Exception:
    st.error("OpenRouter API key not found in the file:  .streamlit/secrets.xml")
    st.stop()

OPENROUTER_API_KEY = api_key
MODEL = "openai/gpt-oss-120b"
CHAT_DIR = "chats"

os.makedirs(CHAT_DIR, exist_ok=True)

# ==========================
# UTILITIES
# ==========================
def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def chat_path(chat_id):
    return os.path.join(CHAT_DIR, f"{chat_id}.json")

def load_chat(chat_id):
    with open(chat_path(chat_id), "r") as f:
        return json.load(f)

def save_chat(chat_id, data):
    with open(chat_path(chat_id), "w") as f:
        json.dump(data, f, indent=2)

def list_chats():
    chats = []
    for file in os.listdir(CHAT_DIR):
        with open(os.path.join(CHAT_DIR, file), "r") as f:
            data = json.load(f)
            chats.append((file.replace(".json", ""), data["title"]))
    return chats

# ==========================
# SESSION STATE
# ==========================
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None

if "messages" not in st.session_state:
    st.session_state.messages = []

# ==========================
# SIDEBAR
# ==========================
with st.sidebar:
    st.title("💬 Conversations")

    if st.button("+ New Chat", use_container_width=True):
        chat_id = str(uuid.uuid4())
        st.session_state.current_chat_id = chat_id
        st.session_state.messages = []
        save_chat(chat_id, {
            "title": "New Chat",
            "messages": []
        })

    st.divider()
    st.subheader("Chat History")

    for chat_id, title in list_chats():
        col1, col2 = st.columns([5, 1])
        with col1:
            if st.button(title, key=chat_id, use_container_width=True):
                st.session_state.current_chat_id = chat_id
                chat = load_chat(chat_id)
                st.session_state.messages = chat["messages"]
        with col2:
            if st.button("🗑️", key=f"del_{chat_id}"):
                os.remove(chat_path(chat_id))
                if st.session_state.current_chat_id == chat_id:
                    st.session_state.current_chat_id = None
                    st.session_state.messages = []
                st.rerun()

    st.divider()

    if st.button("Clear Current Chat", use_container_width=True):
        if st.session_state.current_chat_id:
            save_chat(st.session_state.current_chat_id, {
                "title": "New Chat",
                "messages": []
            })
            st.session_state.messages = []

    #st.toggle("Dark mode", value=True)

# ==========================
# MAIN UI
# ==========================
if st.session_state.current_chat_id is None:
    st.markdown("## 👋 Start a new chat")
    st.stop()

chat_data = load_chat(st.session_state.current_chat_id)

# Title
st.markdown(f"## 🤖 {chat_data['title']}")

# Optional summary
with st.expander("📝 Summarize Conversation"):
    if st.button("Generate Summary"):
        if len(st.session_state.messages) == 0:
            st.info("Nothing to summarize yet.")
        else:
            prompt = "Summarize the following conversation:\n\n"
            for m in st.session_state.messages:
                prompt += f"{m['role']}: {m['content']}\n"

            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": MODEL,
                    "messages": [{"role": "user", "content": prompt}]
                }
            ).json()

            st.success(response["choices"][0]["message"]["content"])

st.divider()

# ==========================
# CHAT MESSAGES
# ==========================
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        st.caption(msg["timestamp"])

# ==========================
# USER INPUT
# ==========================
user_input = st.chat_input("What would you like to know?")

if user_input:
    user_msg = {
        "role": "user",
        "content": user_input,
        "timestamp": now()
    }
    st.session_state.messages.append(user_msg)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": MODEL,
                    "messages": [
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.messages
                    ]
                }
            ).json()

            assistant_text = response["choices"][0]["message"]["content"]

            st.markdown(assistant_text)

    assistant_msg = {
        "role": "assistant",
        "content": assistant_text,
        "timestamp": now()
    }
    st.session_state.messages.append(assistant_msg)

    # Update title automatically
    if chat_data["title"] == "New Chat":
        chat_data["title"] = user_input[:30]

    chat_data["messages"] = st.session_state.messages
    save_chat(st.session_state.current_chat_id, chat_data)

    st.rerun()
