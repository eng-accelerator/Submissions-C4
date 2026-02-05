import streamlit as st
import json
import uuid
import time
import os
from openai import OpenAI

# ------------------ CONFIG ------------------

STORAGE_FILE = "storage.json"
MODEL = "openai/gpt-oss-120b"

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

# ------------------ STORAGE ------------------

def load_storage():
    if not os.path.exists(STORAGE_FILE):
        return {}
    with open(STORAGE_FILE, "r") as f:
        return json.load(f)

def save_storage(data):
    with open(STORAGE_FILE, "w") as f:
        json.dump(data, f, indent=2)

storage = load_storage()

# ------------------ SESSION INIT ------------------

if "chat_id" not in st.session_state:
    st.session_state.chat_id = str(uuid.uuid4())
    storage[st.session_state.chat_id] = {
        "created_at": time.time(),
        "messages": []
    }
    save_storage(storage)

# ------------------ SIDEBAR ------------------

st.sidebar.title("💬 Conversations")

# New Chat
if st.sidebar.button("➕ New Chat"):
    st.session_state.chat_id = str(uuid.uuid4())
    storage[st.session_state.chat_id] = {
        "created_at": time.time(),
        "messages": []
    }
    save_storage(storage)
    st.rerun()

# Chat list
for cid, chat in storage.items():
    if st.sidebar.button(f"🗂️ {cid[:8]}", key=cid):
        st.session_state.chat_id = cid
        st.rerun()

# Delete Chat
if st.sidebar.button("🗑️ Delete Current Chat"):
    storage.pop(st.session_state.chat_id, None)
    save_storage(storage)
    st.session_state.chat_id = str(uuid.uuid4())
    storage[st.session_state.chat_id] = {
        "created_at": time.time(),
        "messages": []
    }
    save_storage(storage)
    st.rerun()

# Clear Chat
if st.sidebar.button("🧹 Clear Current Chat"):
    storage[st.session_state.chat_id]["messages"] = []
    save_storage(storage)
    st.rerun()

# Session Duration
created = storage[st.session_state.chat_id]["created_at"]
duration = int(time.time() - created)
st.sidebar.markdown(f"⏱️ **Session Duration:** {duration}s")

# Export Chat
if st.sidebar.button("📥 Export Chat (.txt)"):
    messages = storage[st.session_state.chat_id]["messages"]
    content = "\n\n".join(
        f"{m['role'].upper()}: {m['content']}" for m in messages
    )
    st.sidebar.download_button(
        label="Download",
        data=content,
        file_name="chat.txt",
        mime="text/plain"
    )

# ------------------ MAIN UI ------------------

st.title("🤖 Chatbot")

messages = storage[st.session_state.chat_id]["messages"]

for msg in messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ------------------ CHAT INPUT ------------------

prompt = st.chat_input("Type your message...")

if prompt:
    messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages
        )
        reply = response.choices[0].message.content
        st.markdown(reply)

    messages.append({"role": "assistant", "content": reply})
    save_storage(storage)
    st.rerun()

# ------------------ SUMMARY EXPANDER ------------------

if messages:
    with st.expander("📌 Chat Summary"):
        summary_prompt = [
            {"role": "system", "content": "Summarize this conversation briefly."},
            *messages
        ]

        summary = client.chat.completions.create(
            model=MODEL,
            messages=summary_prompt
        ).choices[0].message.content

        st.markdown(summary)
