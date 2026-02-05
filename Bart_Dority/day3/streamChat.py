import streamlit as st
from datetime import datetime
from openai import OpenAI
import requests
import json
import uuid


def load_css(path):
    with open(path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css("styles.css")

MODEL_NAME = "openai/gpt-oss-120b"

# -----------------------------
# Page config
# -----------------------------
st.set_page_config(
    page_title="This is a cool assistant!",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------
# Load API Key
# -----------------------------
try:
    api_key = st.secrets["OPENROUTER_API_KEY"]
except KeyError:
    st.error("OPENROUTER_API_KEY not found")
    st.stop()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
    default_headers={
        "HTTP-Referer": "http://localhost:8501",
        "X-Title": "My ChatBot",
    }
)

# -----------------------------
# Helpers
# -----------------------------
def now_ts():
    return datetime.now().strftime("%H:%M:%S")

def generate_chat_title(messages):
    user_msgs = [m["content"] for m in messages if m["role"] == "user"]
    if not user_msgs:
        return "New Chat"
    text = " ".join(user_msgs[:3])
    return text[:40] + "..." if len(text) > 40 else text

def create_new_chat():
    chat_id = str(uuid.uuid4())
    st.session_state.chats[chat_id] = {
        "title": "New Chat",
        "messages": [{
            "role": "assistant",
            "content": "Hello! I'm your demo assistant. How can I help you today?",
            "timestamp": now_ts()
        }],
        "created_at": datetime.now()
    }
    st.session_state.active_chat_id = chat_id

RESPONSE_STYLE_PROMPTS = {
    "Friendly": "Respond in a warm, friendly, and approachable tone.",
    "Professional": "Respond in a formal, professional, and business-appropriate tone.",
    "Concise": "Respond briefly and concisely. Avoid unnecessary explanation.",
    "Verbose": "Respond with detailed explanations and thorough reasoning.",

    "Technical": "Respond with precise technical language, assuming an experienced audience.",
    "Beginner-Friendly": "Explain concepts simply, assuming no prior knowledge.",
    "Direct": "Respond plainly and directly. No filler or hedging.",
    "Analytical": "Break the answer into logical steps and explain the reasoning.",
    "Socratic": "Respond by asking guiding questions before giving conclusions.",
    "Critical": "Challenge assumptions and point out potential flaws or edge cases.",
    "Creative": "Respond imaginatively, using metaphors or novel examples when helpful.",
    "Neutral": "Respond in a factual, neutral tone without opinions.",
    "Persuasive": "Respond with the goal of convincing the reader using logical arguments.",
    "Action-Oriented": "Focus on concrete next steps and actionable advice."
}
# -----------------------------
# Session state init
# -----------------------------
if "chats" not in st.session_state:
    st.session_state.chats = {}
    create_new_chat()

if "active_chat_id" not in st.session_state:
    create_new_chat()

if "start_time" not in st.session_state:
    st.session_state.start_time = datetime.now()

# -----------------------------
# Sidebar
# -----------------------------
with st.sidebar:
    # 🔝 NEW: Conversations
    st.markdown("## 💬 Conversations")

    if st.button("➕ New Chat", use_container_width=True):
        create_new_chat()
        st.rerun()

    st.markdown("### Chat History")

    for chat_id, chat in sorted(
        st.session_state.chats.items(),
        key=lambda x: x[1]["created_at"],
        reverse=True
    ):
        col1, col2 = st.columns([5, 1])

        with col1:
            if st.button(
                chat["title"],
                key=f"select_{chat_id}",
                use_container_width=True
            ):
                st.session_state.active_chat_id = chat_id
                st.rerun()

        with col2:
            if st.button("🗑️", key=f"delete_{chat_id}"):
                del st.session_state.chats[chat_id]
                if chat_id == st.session_state.active_chat_id:
                    create_new_chat()
                st.rerun()

    st.markdown("---")

    # 👇 EXISTING CONFIG (UNCHANGED)
    st.markdown("## ⚙️ Configuration")

    assistant_name = st.text_input(
        "Assistant Name:",
        value="This is a cool assistant!",
    )

    response_style = st.selectbox(
        "Response Style:",
         list(RESPONSE_STYLE_PROMPTS.keys()),  # dynamically pulls all style names,
        index=0,
    )

    max_history = st.slider(
        "Max Chat History:",
        min_value=5,
        max_value=100,
        value=40,
    )

    show_timestamps = st.checkbox("Show Timestamps", value=True)

    st.markdown("---")
    st.markdown("### 📊 Session Stats")

    duration = datetime.now() - st.session_state.start_time
    st.metric("Session Duration", f"{duration.seconds // 60}m {duration.seconds % 60}s")
    st.metric("Total Chats", len(st.session_state.chats))
    st.metric(
        "Total Messages",
        sum(len(c["messages"]) for c in st.session_state.chats.values())
    )

# -----------------------------
# Main Header
# -----------------------------
st.markdown(f"# 🚀 {assistant_name}")
st.caption(f"Response Style: **{response_style}** | History Limit: **{max_history} messages**")

# -----------------------------
# Active Chat
# -----------------------------
current_chat = st.session_state.chats[st.session_state.active_chat_id]
messages = current_chat["messages"]

# -----------------------------
# Chat history
# -----------------------------
for msg in messages[-max_history:]:
    with st.chat_message(msg["role"]):
        if show_timestamps and "timestamp" in msg:
            st.caption(msg["timestamp"])

        # Show response style label for assistant messages
        if msg["role"] == "assistant" and "response_style" in msg:
            st.markdown(
                f"<div class='response-style-label'>"
                f"Response Style: <strong>{msg['response_style']}</strong>"
                f"</div>",
                unsafe_allow_html=True
            )

        st.write(msg["content"])

# -----------------------------
# OpenRouter API Call
# -----------------------------
def get_ai_response(messages):
    url = "https://openrouter.ai/api/v1/chat/completions"

    style_prompt = RESPONSE_STYLE_PROMPTS.get(
        response_style,
        "Respond helpfully and clearly."
    )

    clean_messages = [
        {
            "role": "system",
            "content": f"You are a helpful assistant. {style_prompt}"
        }
    ] + [
        {"role": m["role"], "content": m["content"]}
        for m in messages
    ]


    payload = {
        "model": MODEL_NAME,
        "messages": clean_messages
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    print(messages)
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code != 200:
        return f"Error: {response.text}"

    return response.json()["choices"][0]["message"]["content"]

# -----------------------------
# Chat input
# -----------------------------
user_input = st.chat_input(f"Message {assistant_name}...")

if user_input:
    messages.append({
        "role": "user",
        "content": user_input,
        "timestamp": now_ts()
    })

    assistant_reply = get_ai_response(messages)

    messages.append({
        "role": "assistant",
        "content": assistant_reply,
        "response_style": response_style,
        "timestamp": now_ts()
    })

    current_chat["title"] = generate_chat_title(messages)

    st.rerun()

# -----------------------------
# Expandable sections
# -----------------------------
st.markdown("---")

with st.expander("ℹ️ About This Demo"):
    st.write(
        "This is a Streamlit-based assistant UI scaffold. "
        "It demonstrates multi-chat management, sidebar navigation, "
        "and session-aware state."
    )

with st.expander("📓 Instructor Notes"):
    st.write(
        "- Replace summarizer with LLM-based title generation\n"
        "- Persist chats to disk or DB\n"
        "- Add streaming responses"
    )

with st.expander("🛠 Development Info"):
    st.json({
        "active_chat_id": st.session_state.active_chat_id,
        "total_chats": len(st.session_state.chats),
        "messages_in_active_chat": len(messages),
    })

