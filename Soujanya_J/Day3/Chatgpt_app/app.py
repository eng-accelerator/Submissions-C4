import json
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests
import streamlit as st
import streamlit.components.v1 as components


# -----------------------------
# Config
# -----------------------------
APP_STORAGE_KEY = "chatbot_style_app_state_v1"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_ID = "openai/gpt-oss-120b"

# Optional OpenRouter recommended headers (helps routing/analytics)
APP_TITLE = "Hey who are you ?"
APP_HTTP_REFERER = "http://localhost:8501"
APP_X_TITLE = "Streamlit Chatbot"


# -----------------------------
# Browser localStorage bridge
# -----------------------------
def local_storage_get(storage_key: str) -> Optional[Dict[str, Any]]:
    """
    Reads JSON from browser localStorage[storage_key] and returns as dict.
    Uses a tiny Streamlit component that returns the value via setComponentValue.
    """
    html = f"""
    <script>
      const key = {json.dumps(storage_key)};
      const raw = window.localStorage.getItem(key);
      let parsed = null;
      try {{
        parsed = raw ? JSON.parse(raw) : null;
      }} catch (e) {{
        parsed = null;
      }}
      // Send to Streamlit
      const out = {{ value: parsed }};
      window.parent.postMessage({{ isStreamlitMessage: true, type: "streamlit:setComponentValue", value: out }}, "*");
    </script>
    """
    res = components.html(html, height=0)
    # Streamlit returns whatever setComponentValue sends
    if isinstance(res, dict) and "value" in res:
        return res["value"]
    return None


def local_storage_set(storage_key: str, value: Dict[str, Any]) -> None:
    """
    Writes JSON to browser localStorage[storage_key].
    """
    payload = json.dumps(value)
    html = f"""
    <script>
      const key = {json.dumps(storage_key)};
      const val = {json.dumps(payload)};
      window.localStorage.setItem(key, val);
      // ack (optional)
      window.parent.postMessage({{
        isStreamlitMessage: true,
        type: "streamlit:setComponentValue",
        value: {{ ok: true, ts: Date.now() }}
      }}, "*");
    </script>
    """
    components.html(html, height=0)


# -----------------------------
# Data model
# -----------------------------
@dataclass
class Chat:
    chat_id: str
    title: str
    messages: List[Dict[str, str]]  # {"role": "user"|"assistant", "content": "..."}
    summary: Optional[str] = None
    created_at: float = 0.0
    updated_at: float = 0.0


def now_ts() -> float:
    return time.time()


def new_chat(title: str = "New Chat") -> Chat:
    cid = str(uuid.uuid4())
    t = now_ts()
    return Chat(chat_id=cid, title=title, messages=[], summary=None, created_at=t, updated_at=t)


def serialize_state(chats: Dict[str, Chat], active_chat_id: Optional[str]) -> Dict[str, Any]:
    return {
        "active_chat_id": active_chat_id,
        "chats": {
            cid: {
                "chat_id": c.chat_id,
                "title": c.title,
                "messages": c.messages,
                "summary": c.summary,
                "created_at": c.created_at,
                "updated_at": c.updated_at,
            }
            for cid, c in chats.items()
        },
        "version": 1,
    }


def hydrate_state(raw: Dict[str, Any]) -> (Dict[str, Chat], Optional[str]):
    chats: Dict[str, Chat] = {}
    active = raw.get("active_chat_id")
    raw_chats = raw.get("chats", {}) or {}
    for cid, c in raw_chats.items():
        chats[cid] = Chat(
            chat_id=c.get("chat_id", cid),
            title=c.get("title", "Chat"),
            messages=c.get("messages", []) or [],
            summary=c.get("summary"),
            created_at=float(c.get("created_at", now_ts())),
            updated_at=float(c.get("updated_at", now_ts())),
        )
    if active not in chats:
        active = next(iter(chats.keys()), None)
    return chats, active


# -----------------------------
# OpenRouter (streaming)
# -----------------------------
def openrouter_headers() -> Dict[str, str]:
    api_key = st.secrets.get("OPENROUTER_API_KEY", "")
    if not api_key:
        st.error("Missing OPENROUTER_API_KEY in .streamlit/secrets.toml")
        st.stop()

    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": APP_HTTP_REFERER,
        "X-Title": APP_X_TITLE,
    }


def stream_chat_completion(messages: List[Dict[str, str]]) -> str:
    """
    Streams assistant text using OpenRouter's OpenAI-compatible SSE.
    Returns final assistant text.
    """
    body = {
        "model": MODEL_ID,
        "messages": messages,
        "stream": True,
        "temperature": 0.7,
    }

    r = requests.post(
        OPENROUTER_URL,
        headers=openrouter_headers(),
        data=json.dumps(body),
        stream=True,
        timeout=120,
    )
    r.raise_for_status()

    full_text = ""
    for line in r.iter_lines(decode_unicode=True):
        if not line:
            continue
        if line.startswith("data: "):
            data = line[len("data: ") :].strip()
            if data == "[DONE]":
                break
            try:
                evt = json.loads(data)
                delta = evt["choices"][0]["delta"].get("content", "")
                if delta:
                    full_text += delta
                    yield delta
            except Exception:
                # ignore malformed events
                continue

    return full_text


def summarize_chat(messages: List[Dict[str, str]]) -> str:
    """
    Non-stream summary (small and fast). Uses same model.
    """
    prompt = (
        "Summarize this conversation in 3-6 bullet points. "
        "Be concise and capture key decisions, questions, and outcomes."
    )
    body = {
        "model": MODEL_ID,
        "messages": [
            {"role": "system", "content": "You are a concise summarizer."},
            {"role": "user", "content": prompt},
            {"role": "user", "content": json.dumps(messages, ensure_ascii=False)},
        ],
        "stream": False,
        "temperature": 0.2,
    }
    r = requests.post(
        OPENROUTER_URL,
        headers=openrouter_headers(),
        data=json.dumps(body),
        timeout=120,
    )
    r.raise_for_status()
    data = r.json()
    return data["choices"][0]["message"]["content"].strip()


# -----------------------------
# UI styling (dark, screenshot-like)
# -----------------------------
def inject_css():
    st.markdown(
        """
        <style>
        /* -----------------------------
           Theme variables (tweak here)
        ------------------------------*/
        :root{
          --bg: #0f1115;
          --panel: #141720;
          --card: rgba(255,255,255,0.03);
          --border: rgba(255,255,255,0.10);
          --border2: rgba(255,255,255,0.16);
          --text: #e8eaf0;
          --muted: rgba(232,234,240,0.70);
          --placeholder: rgba(232,234,240,0.45);
          --hoverbg: rgba(255,255,255,0.08);
          --focusring: rgba(255,255,255,0.22);
        }

        /* Base */
        .stApp { background: var(--bg); color: var(--text); }

        /* Sidebar */
        section[data-testid="stSidebar"] {
          background: var(--panel);
          border-right: 1px solid rgba(255,255,255,0.06);
        }

        /* -----------------------------
           ✅ FIX #1: Chat Input readability
           (text, caret, placeholder, focus)
        ------------------------------*/
        div[data-testid="stChatInput"] textarea {
          background: rgba(255,255,255,0.06) !important;
          color: var(--text) !important;             /* typed text */
          caret-color: var(--text) !important;       /* cursor */
          border: 1px solid var(--border) !important;
          border-radius: 999px !important;
          outline: none !important;
        }

        /* placeholder text */
        div[data-testid="stChatInput"] textarea::placeholder {
          color: var(--placeholder) !important;
          opacity: 1 !important;
        }

        /* focus state */
        div[data-testid="stChatInput"] textarea:focus {
          border-color: var(--border2) !important;
          box-shadow: 0 0 0 3px var(--focusring) !important;
        }

        /* some Streamlit versions wrap input differently; keep it safe */
        div[data-testid="stChatInput"] * {
          color: inherit;
        }

        /* -----------------------------
           ✅ FIX #2: Expander header hover unreadable
           Streamlit expander = <details><summary>...</summary>...</details>
        ------------------------------*/
        div[data-testid="stExpander"] details {
          border: 1px solid rgba(255,255,255,0.08) !important;
          border-radius: 12px !important;
          background: rgba(255,255,255,0.02) !important;
        }

        /* summary/header text */
        div[data-testid="stExpander"] details > summary {
          color: var(--text) !important;
          font-weight: 600 !important;
        }

        /* hover + focus + active states */
        div[data-testid="stExpander"] details > summary:hover,
        div[data-testid="stExpander"] details > summary:focus,
        div[data-testid="stExpander"] details[open] > summary {
          background: var(--hoverbg) !important;
          color: var(--text) !important; /* <-- critical for readability */
          border-radius: 12px !important;
        }

        /* expander body text */
        div[data-testid="stExpander"] .stMarkdown,
        div[data-testid="stExpander"] p,
        div[data-testid="stExpander"] li {
          color: var(--text) !important;
        }

        /* -----------------------------
           Optional: chat bubbles contrast
        ------------------------------*/
        div[data-testid="stChatMessage"] {
          background: var(--card);
          border: 1px solid rgba(255,255,255,0.06);
          border-radius: 14px;
          padding: 12px 14px;
          margin-bottom: 10px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

# -----------------------------
# App init + state
# -----------------------------
st.set_page_config(page_title="Chatbot", layout="wide")
inject_css()

if "loaded_from_local" not in st.session_state:
    st.session_state.loaded_from_local = False

if "chats" not in st.session_state:
    st.session_state.chats: Dict[str, Chat] = {}
if "active_chat_id" not in st.session_state:
    st.session_state.active_chat_id = None


def ensure_loaded():
    if st.session_state.loaded_from_local:
        return

    raw = local_storage_get(APP_STORAGE_KEY)
    if raw:
        chats, active = hydrate_state(raw)
        st.session_state.chats = chats
        st.session_state.active_chat_id = active

    # If nothing existed, create a starter chat
    if not st.session_state.chats:
        c = new_chat("Hey who are you ?")
        st.session_state.chats[c.chat_id] = c
        st.session_state.active_chat_id = c.chat_id

    st.session_state.loaded_from_local = True


def persist():
    local_storage_set(
        APP_STORAGE_KEY,
        serialize_state(st.session_state.chats, st.session_state.active_chat_id),
    )


ensure_loaded()


# -----------------------------
# Sidebar
# -----------------------------
with st.sidebar:
    st.markdown("### Conversations")

    c_new = st.container()
    with c_new:
        st.markdown('<div class="newchat">', unsafe_allow_html=True)
        if st.button("➕  New Chat", use_container_width=True):
            c = new_chat("New Chat")
            st.session_state.chats[c.chat_id] = c
            st.session_state.active_chat_id = c.chat_id
            persist()
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("#### Chat History")

    # show newest first
    chat_items = sorted(
        st.session_state.chats.values(),
        key=lambda x: x.updated_at,
        reverse=True,
    )

    for c in chat_items:
        cols = st.columns([0.82, 0.18], gap="small")
        with cols[0]:
            is_active = (c.chat_id == st.session_state.active_chat_id)
            label = f"🟢 {c.title}" if is_active else f"{c.title}"
            if st.button(label, key=f"sel_{c.chat_id}", use_container_width=True):
                st.session_state.active_chat_id = c.chat_id
                persist()
                st.rerun()
        with cols[1]:
            if st.button("🗑️", key=f"del_{c.chat_id}", help="Delete chat"):
                # delete and pick another active chat
                del st.session_state.chats[c.chat_id]
                if st.session_state.active_chat_id == c.chat_id:
                    st.session_state.active_chat_id = next(iter(st.session_state.chats.keys()), None)
                persist()
                st.rerun()

    st.markdown("---")
    st.markdown("### Settings")

    # (UI-only toggle; Streamlit theme switching is usually via config)
    st.toggle("Dark mode", value=True, disabled=True)

    if st.button("🧹  Clear Current Chat", use_container_width=True):
        aid = st.session_state.active_chat_id
        if aid and aid in st.session_state.chats:
            st.session_state.chats[aid].messages = []
            st.session_state.chats[aid].summary = None
            st.session_state.chats[aid].updated_at = now_ts()
            persist()
            st.rerun()


# -----------------------------
# Main area
# -----------------------------
active_id = st.session_state.active_chat_id
if not active_id or active_id not in st.session_state.chats:
    st.info("No chat selected. Create a new one from the sidebar.")
    st.stop()

chat = st.session_state.chats[active_id]

# Title row + summarize button (like screenshot)
top_cols = st.columns([0.80, 0.20], vertical_alignment="center")
with top_cols[0]:
    st.markdown(f'<div class="main-title">👋 {chat.title}</div>', unsafe_allow_html=True)

with top_cols[1]:
    if st.button("🧾  Summarize Conversation", use_container_width=True):
        if chat.messages:
            with st.spinner("Summarizing..."):
                chat.summary = summarize_chat(chat.messages)
                chat.updated_at = now_ts()
                persist()
                st.rerun()
        else:
            st.toast("Nothing to summarize yet.", icon="ℹ️")

# Optional expander: summary right below title
with st.expander("Summary (optional)", expanded=False):
    if not chat.messages:
        st.caption("No messages yet.")
    else:
        if chat.summary:
            st.markdown(chat.summary)
        else:
            st.caption("No summary saved yet. Click **Summarize Conversation**.")

# Render messages
for m in chat.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Input (bottom)
user_text = st.chat_input("What would you like to know?")
if user_text:
    # Add user msg
    chat.messages.append({"role": "user", "content": user_text})
    chat.updated_at = now_ts()

    # Auto-title first time
    if chat.title == "New Chat" and len(chat.messages) == 1:
        chat.title = user_text[:28] + ("..." if len(user_text) > 28 else "")

    persist()

    # Stream assistant
    with st.chat_message("assistant"):
        placeholder = st.empty()
        acc = ""

        # Build messages for model (you can add a system prompt here if you want)
        model_messages = [{"role": "system", "content": "You are a helpful assistant."}] + chat.messages

        try:
            for delta in stream_chat_completion(model_messages):
                acc += delta
                placeholder.markdown(acc)
        except requests.HTTPError as e:
            st.error(f"OpenRouter error: {e}")
            st.stop()
        except Exception as e:
            st.error(f"Unexpected error: {e}")
            st.stop()

    # Save assistant msg
    chat.messages.append({"role": "assistant", "content": acc})
    chat.updated_at = now_ts()

    # Invalidate summary (optional behavior)
    chat.summary = None

    persist()
    st.rerun()
