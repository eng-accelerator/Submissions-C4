import streamlit as st
from openai import OpenAI
import json
import os
from datetime import datetime

# ------------------------------------------------------
# Page config
# ------------------------------------------------------
st.set_page_config(
    page_title="Chandru's Local Chatbot",
    page_icon="🤖",
    layout="wide",
)

st.title("🤖 Chandru's Local Chatbot (OpenRouter)")

# ------------------------------------------------------
# Constants
# ------------------------------------------------------
CHAT_DIR = "chat_store"
MODEL_NAME = "openai/gpt-oss-120b"

os.makedirs(CHAT_DIR, exist_ok=True)

# ------------------------------------------------------
# API Key
# ------------------------------------------------------
api_key = st.secrets.get("OPENROUTER_API_KEY")

if not api_key:
    api_key = st.sidebar.text_input(
        "Enter OpenRouter API Key",
        type="password"
    )

if not api_key:
    st.warning("Please provide an OpenRouter API key.")
    st.stop()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

# ------------------------------------------------------
# Session state
# ------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat_id" not in st.session_state:
    st.session_state.chat_id = None

if "chat_summary" not in st.session_state:
    st.session_state.chat_summary = ""

# ------------------------------------------------------
# Storage helpers
# ------------------------------------------------------
def summarize_chat(messages):
    if not messages:
        return ""

    prompt = [
        {
            "role": "system",
            "content": "Summarize the following conversation in 3–5 concise bullet points."
        },
        {
            "role": "user",
            "content": json.dumps(messages, indent=2)
        }
    ]

    try:
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            messages=prompt,
        )
        return resp.choices[0].message.content
    except:
        return "Summary unavailable."

def save_chat(messages, chat_id=None):
    if not messages:
        return None

    chat_id = chat_id or datetime.now().strftime("%Y%m%d_%H%M%S")

    title = next(
        (m["content"][:60] for m in messages if m["role"] == "user"),
        "New Chat"
    )

    summary = summarize_chat(messages)

    data = {
        "chat_id": chat_id,
        "title": title,
        "timestamp": datetime.now().isoformat(),
        "messages": messages,
        "summary": summary,
    }

    with open(f"{CHAT_DIR}/{chat_id}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    st.session_state.chat_summary = summary
    return chat_id

def load_chat(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def list_chats():
    chats = []
    for file in os.listdir(CHAT_DIR):
        if file.endswith(".json"):
            path = os.path.join(CHAT_DIR, file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    chats.append(json.load(f))
            except:
                pass
    return sorted(chats, key=lambda x: x["timestamp"], reverse=True)

# ------------------------------------------------------
# 🔽 Chat Summary (UNDER TITLE)
# ------------------------------------------------------
if st.session_state.messages:
    with st.expander("🧠 Chat Summary", expanded=False):
        if st.session_state.chat_summary:
            st.markdown(st.session_state.chat_summary)
        else:
            st.caption("Summary will appear after the first response.")

st.markdown("---")

# ------------------------------------------------------
# Sidebar
# ------------------------------------------------------
st.sidebar.title("💬 Chats")

if st.sidebar.button("➕ New Chat"):
    if st.session_state.messages:
        save_chat(st.session_state.messages, st.session_state.chat_id)
    st.session_state.messages = []
    st.session_state.chat_id = None
    st.session_state.chat_summary = ""
    st.rerun()

if st.sidebar.button("🧹 Clear Current Chat"):
    st.session_state.messages = []
    st.session_state.chat_id = None
    st.session_state.chat_summary = ""
    st.rerun()

st.sidebar.markdown("---")

for chat in list_chats():
    chat_id = chat["chat_id"]

    col1, col2 = st.sidebar.columns([5, 1])

    with col1:
        if st.button(f"💬 {chat['title']}", key=f"load_{chat_id}"):
            st.session_state.messages = chat["messages"]
            st.session_state.chat_id = chat_id
            st.session_state.chat_summary = chat.get("summary", "")
            st.rerun()

    with col2:
        if st.button("🗑", key=f"del_{chat_id}"):
            os.remove(f"{CHAT_DIR}/{chat_id}.json")
            if st.session_state.chat_id == chat_id:
                st.session_state.messages = []
                st.session_state.chat_id = None
                st.session_state.chat_summary = ""
            st.rerun()

# ------------------------------------------------------
# Main Chat UI
# ------------------------------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ------------------------------------------------------
# Chat input
# ------------------------------------------------------
if prompt := st.chat_input("Type your message…"):
    st.session_state.messages.append(
        {"role": "user", "content": prompt}
    )

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=st.session_state.messages,
            )
            answer = response.choices[0].message.content
            st.markdown(answer)

    st.session_state.messages.append(
        {"role": "assistant", "content": answer}
    )

    st.session_state.chat_id = save_chat(
        st.session_state.messages,
        st.session_state.chat_id
    )
# ------------------------------------------------------