import streamlit as st
import os
import json
import requests
from datetime import datetime

# --- CONFIG ---
CONFIG_PATH = "config.json"
CHATS_DIR = "chats"

# --- UTILS ---
def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {"openrouter_api_key": "", "model": "openai/gpt-oss-120b"}
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)

def list_chats():
    if not os.path.exists(CHATS_DIR):
        os.makedirs(CHATS_DIR)
    return sorted([f[:-5] for f in os.listdir(CHATS_DIR) if f.endswith(".json")])

def load_chat(chat_id):
    path = os.path.join(CHATS_DIR, f"{chat_id}.json")
    if not os.path.exists(path):
        return {"title": chat_id, "messages": []}
    with open(path, "r") as f:
        return json.load(f)

def save_chat(chat_id, chat_data):
    path = os.path.join(CHATS_DIR, f"{chat_id}.json")
    with open(path, "w") as f:
        json.dump(chat_data, f, indent=2)

def delete_chat(chat_id):
    path = os.path.join(CHATS_DIR, f"{chat_id}.json")
    if os.path.exists(path):
        os.remove(path)

def summarize_chat(messages, api_key, model):
    if not messages:
        return "No messages to summarize."
    prompt = "Summarize the following conversation in plain English:\n" + "\n".join([
        f"User: {m['user']}\nAI: {m['ai']}" if 'ai' in m else f"User: {m['user']}" for m in messages
    ])
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 256,
        "temperature": 0.5
    }
    try:
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Summary error: {e}"

def query_openrouter(user_message, api_key, model):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model,
        "messages": [
            {"role": "user", "content": user_message}
        ],
        "max_tokens": 512,
        "temperature": 0.7
    }
    try:
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=60
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"API error: {e}"

# --- MAIN APP ---
st.set_page_config(page_title="Hey who are you ?", layout="wide")
config = load_config()

if "api_key" not in st.session_state:
    st.session_state.api_key = config.get("openrouter_api_key", "")
if "model" not in st.session_state:
    st.session_state.model = config.get("model", "openai/gpt-oss-120b")

# --- SIDEBAR ---
st.sidebar.title(":speech_balloon: Conversations")
chat_ids = list_chats()
selected_chat = st.sidebar.radio(
    "Chat History", chat_ids, index=0 if chat_ids else None, key="selected_chat_radio"
)

if st.sidebar.button("New Chat"):
    new_id = datetime.now().strftime("%Y%m%d%H%M%S")
    save_chat(new_id, {"title": f"Chat {new_id}", "messages": []})
    st.rerun()

if selected_chat and st.sidebar.button("Delete Chat"):
    delete_chat(selected_chat)
    st.rerun()

if selected_chat and st.sidebar.button("Clear Current Chat"):
    chat_data = load_chat(selected_chat)
    chat_data["messages"] = []
    save_chat(selected_chat, chat_data)
    st.rerun()

with st.sidebar.expander("Settings"):
    api_key = st.text_input("OpenRouter API Key", st.session_state.api_key, type="password")
    if st.button("Save API Key"):
        st.session_state.api_key = api_key
        config["openrouter_api_key"] = api_key
        save_config(config)
        st.success("API Key saved!")

# --- MAIN CHAT UI ---
if selected_chat:
    chat_data = load_chat(selected_chat)
    st.title(chat_data["title"])
    with st.expander("Summarize Conversation", expanded=True):
        summary = summarize_chat(chat_data["messages"], st.session_state.api_key, st.session_state.model)
        st.write(summary)
    st.markdown("---")
    for msg in chat_data["messages"]:
        st.markdown(f"**You:** {msg['user']}")
        if "ai" in msg:
            st.markdown(f"**AI:** {msg['ai']}")
        st.markdown("---")
    user_input = st.text_input("What would you like to know?", key="user_input")
    if st.button("Send") and user_input:
        ai_response = query_openrouter(user_input, st.session_state.api_key, st.session_state.model)
        chat_data["messages"].append({"user": user_input, "ai": ai_response})
        save_chat(selected_chat, chat_data)
        st.rerun()
else:
    st.title("Hey who are you ?")
    st.info("Create or select a chat from the sidebar.")
