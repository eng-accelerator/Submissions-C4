import streamlit as st
import time
import random
from textwrap import shorten
import re
import os
import json
from openai import OpenAI

st.title("Hey who are you?")
# Summarize UI is shown after conversations are initialized to avoid session-state access issues.

# --- Sidebar: Conversations (stored on disk) ---
CHAT_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), "Chat_history")
os.makedirs(CHAT_DIR, exist_ok=True)

def conv_path(cid):
    return os.path.join(CHAT_DIR, f"conv_{cid}.json")

def write_conv(conv):
    """Write conversation JSON atomically: write to a temp file then replace."""
    path = conv_path(conv["id"])
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(conv, f, ensure_ascii=False, indent=2)
        f.flush()
        os.fsync(f.fileno())
    # atomic replace
    os.replace(tmp, path)

def load_conv_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_conversations_from_disk():
    files = [os.path.join(CHAT_DIR, f) for f in os.listdir(CHAT_DIR) if f.endswith(".json")]
    if not files:
        defaults = [
            {"id": 1, "title": "Hey who are you ?", "active": True, "messages": []},
            {"id": 2, "title": "This is a new chat to test the chat history function", "active": False, "messages": []},
            {"id": 3, "title": "Hello who are you?", "active": False, "messages": []},
            {"id": 4, "title": "Teach me about the Mathematics of Class 12", "active": False, "messages": []},
            {"id": 5, "title": "New Chat", "active": False, "messages": []},
            {"id": 6, "title": "Hello", "active": False, "messages": []},
        ]
        for d in defaults:
            write_conv(d)
        return defaults
    convs = [load_conv_file(p) for p in files]
    convs.sort(key=lambda c: (not c.get("active", False), c.get("id", 0)))
    return convs

if "conversations" not in st.session_state:
    st.session_state.conversations = load_conversations_from_disk()
    maxid = max((c["id"] for c in st.session_state.conversations), default=0)
    st.session_state.next_conv_id = maxid + 1

# Initialize per-session messages from the active conversation
if "messages" not in st.session_state:
    active_conv = next((c for c in st.session_state.conversations if c.get("active")), None)
    if active_conv:
        st.session_state.messages = active_conv.get("messages", []).copy()
    else:
        st.session_state.messages = []


# --- OpenAI / client config (required before using summarizer) ---
MODEL = "openai/gpt-oss-120b"  # model used for conversation; summarization uses same model
DEFAULT_SUMMARY_MAX_TOKENS = 200

# Prefer environment key if set; fall back to the embedded key if present
api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY_PATH")

if not api_key:
    st.warning("Please provide your OpenAI/OpenRouter API key via the OPENAI_API_KEY environment variable.")
    st.stop()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
    default_headers={
        "HTTP-Referer": "http://localhost:8501",
        "X-Title": "My ChatBot",
    }
)


def summarize_conversation_with_model(messages, max_tokens=DEFAULT_SUMMARY_MAX_TOKENS):
    """Summarize conversation messages using the configured client and MODEL."""
    if not messages:
        return ""
    sys_msg = {"role": "system", "content": "You are a concise assistant. Summarize the following conversation into a short paragraph (3-5 sentences) highlighting the main points and any action items. Keep it brief."}
    msgs = [sys_msg] + [{"role": m.get("role", "user"), "content": m.get("content", m.get("text", ""))} for m in messages]
    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=msgs,
            max_tokens=max_tokens,
            temperature=0.2,
        )
        # Extract the content from response in a couple of common shapes
        content = ""
        if hasattr(resp, "choices") and resp.choices:
            ch = resp.choices[0]
            if getattr(ch, "message", None):
                content = ch.message.get("content", "") if isinstance(ch.message, dict) else ch.message.content
            elif getattr(ch, "delta", None):
                content = ch.delta.get("content", "") if isinstance(ch.delta, dict) else ch.delta.content
            else:
                content = str(ch)
        else:
            content = str(resp)
        return content.strip()
    except Exception as e:
        st.error(f"Summarization failed: {e}")
        return ""


def generate_title_from_messages(messages):
    """Generate a short, meaningful title from conversation messages."""
    if not messages:
        return "New Chat"
    cand = ""
    # prefer the first user message
    for m in messages:
        if m.get("role") == "user" and m.get("content"):
            cand = m.get("content").strip()
            break
    # fallback to any message content
    if not cand:
        for m in messages:
            if m.get("content"):
                cand = m.get("content").strip()
                break
    if not cand:
        return "New Chat"
    first_sent = re.split(r'(?<=[.!?])\s+', cand)[0]
    title = shorten(first_sent, width=36, placeholder='...')
    title = title.strip().rstrip('.!?')
    return title or "New Chat"


def update_conv_title_if_needed(conv, messages):
    """Update conversation title if it's a default/generic title."""
    new_title = generate_title_from_messages(messages)
    cur = conv.get("title", "") or ""
    if cur.lower().startswith("new chat") or len(cur.strip()) < 6:
        conv["title"] = new_title
        write_conv(conv)

# --- Summarize Conversation expander (after conversations are initialized) ---
with st.expander("Summarize Conversation"):
    st.subheader("Conversation Summary")
    selected_conv = next((c for c in st.session_state.conversations if c.get("active")), None)
    if selected_conv:
        prev = selected_conv.get("summary")
        if prev:
            st.markdown("**Saved summary:**")
            st.write(prev)
        if st.button("🔍 Summarize Conversation", key="summarize_btn"):
            stored = selected_conv.get("messages", []) or []
            live = st.session_state.get("messages", []) or []
            # Merge stored + live messages (live may be the session in-memory messages)
            messages = stored + live
            if not any(m.get("content") or m.get("text") for m in messages):
                st.warning("No messages to summarize.")
            else:
                with st.spinner("Summarizing conversation using the conversation model..."):
                    summary = summarize_conversation_with_model(messages)
                    if summary:
                        selected_conv["summary"] = summary
                        write_conv(selected_conv)
                        st.success("Summary saved to conversation")
                        st.write(summary)
                    else:
                        st.warning("No summary produced by the model.")
    else:
        st.info("No conversation selected")




def safe_rerun():
    """Rerun the app in a way compatible across Streamlit versions."""
    try:
        # preferred method (may not exist on some versions)
        if hasattr(st, "experimental_rerun"):
            st.experimental_rerun()
            return
    except Exception:
        pass
    # Fallback: update a query param to force a rerun (use st.query_params API)
    try:
        params = dict(st.query_params)
        params["_rerun"] = [str(time.time())]
        # assign back to st.query_params to update the URL
        st.query_params = params
    except Exception:
        # Last resort: do nothing (no-op)
        return


def new_chat():
    # Insert new conversation at top and make it active (persist to disk)
    nid = st.session_state.next_conv_id
    conv = {"id": nid, "title": "New Chat", "active": True, "messages": []}
    # mark others inactive and persist
    for c in st.session_state.conversations:
        if c.get("active"):
            c["active"] = False
            write_conv(c)
    # write new conversation and add to session state
    write_conv(conv)
    st.session_state.conversations.insert(0, conv)
    st.session_state.next_conv_id += 1
    st.session_state.messages = []
    safe_rerun()


def select_chat(cid: int):
    for c in st.session_state.conversations:
        c["active"] = (c["id"] == cid)
        write_conv(c)
        if c["active"]:
            st.session_state.messages = c.get("messages", []).copy()
    safe_rerun()


def delete_chat(cid: int):
    # remove file on disk
    p = conv_path(cid)
    if os.path.exists(p):
        os.remove(p)
    st.session_state.conversations = [c for c in st.session_state.conversations if c["id"] != cid]
    # ensure at least one active and persist
    if st.session_state.conversations and not any(c.get("active") for c in st.session_state.conversations):
        st.session_state.conversations[0]["active"] = True
        write_conv(st.session_state.conversations[0])
    # Sync session messages to the current active conversation (if any)
    active = next((c for c in st.session_state.conversations if c.get("active")), None)
    st.session_state.messages = active.get("messages", []).copy() if active else []
    safe_rerun()

with st.sidebar:
    st.markdown("## 💬 Conversations")

    if st.button("+ New Chat", key="new_conv_btn"):
        new_chat()

    st.markdown("---")
    st.markdown("**Chat History**")

    # Display chat items with a delete button on the right
    for c in st.session_state.conversations:
        cols = st.columns([0.9, 0.1])
        with cols[0]:
            prefix = "🟢 " if c.get("active") else ""
            label = prefix + shorten(c["title"], width=36, placeholder="...")
            if st.button(label, key=f"select_{c['id']}"):
                select_chat(c["id"])
        with cols[1]:
            if st.button("🗑️", key=f"del_{c['id']}"):
                delete_chat(c["id"])

 
    st.markdown("## ⚙️ Settings")

    # Clear current chat button
    if st.button("🗑️ Clear Current Chat", key="clear_current_chat"):
        selected = next((c for c in st.session_state.conversations if c.get("active")), None)
        if selected:
            selected["messages"] = []
            write_conv(selected)
            st.session_state.messages = []
            st.success("Cleared current chat messages")
        else:
            st.warning("No conversation selected")

# --- Main area: show selected conversation title ---
selected = next((c for c in st.session_state.conversations if c.get("active")), None)
if selected:
    st.subheader(f"Conversation: {selected['title']}")
else:
    st.subheader("No conversation selected")





# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle user input
if prompt := st.chat_input("What would you like to know?"):
    # Add user message to chat history (session + persistent conversation)
    st.session_state.messages.append({"role": "user", "content": prompt})
    selected = next((c for c in st.session_state.conversations if c.get("active")), None)
    if selected:
        selected.setdefault("messages", []).append({"role": "user", "content": prompt})
        # update conversation title based on content
        update_conv_title_if_needed(selected, selected["messages"])
        write_conv(selected)

    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate AI response
    with st.chat_message("assistant"):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=st.session_state.messages,
                stream=True,
                extra_headers={
                    "HTTP-Referer": "http://localhost:8501",
                    "X-Title": "My ChatBot"
                },
                extra_body={
                    "provider": {
                        "data_collection": "deny"  # or "allow" if you permit retention
                    }
                }
            )
            response_text = ""
            response_placeholder = st.empty()

            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    # Clean up unwanted tokens
                    content = chunk.choices[0].delta.content
                    content = (
                        content.replace('<s>', '')
                        .replace('<|im_start|>', '')
                        .replace('<|im_end|>', '')
                        .replace("<|OUT|>", "")
                    )
                    response_text += content
                    response_placeholder.markdown(response_text + "▌")

            # Final cleanup of response text
            response_text = (
                response_text.replace('<s>', '')
                .replace('<|im_start|>', '')
                .replace('<|im_end|>', '')
                .replace("<|OUT|>", "")
                .strip()
            )
            response_placeholder.markdown(response_text)

            # Add assistant response to chat history (session + persistent conversation)
            st.session_state.messages.append({"role": "assistant", "content": response_text})
            if selected:
                selected.setdefault("messages", []).append({"role": "assistant", "content": response_text})
                # update title if it's still generic
                update_conv_title_if_needed(selected, selected["messages"])
                write_conv(selected)


        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.info("Please check your API key and try again.")





