"""
Floating Chat Widget
━━━━━━━━━━━━━━━━━━━
A floating chat bubble (bottom-right) with a chat panel in the RAG Visualizations tab.

Think of it like the "Need help?" chat icon on your banking app —
always there in the corner, opens a conversation panel when you need it.
"""

from __future__ import annotations
from typing import Dict, Any
import streamlit as st
import streamlit.components.v1 as components
from agents.report_chat import chat as report_chat

# ── Suggested prompts shown before first message ──────────────────────
_SUGGESTIONS = [
    "What were the main findings?",
    "Which claims were verified?",
    "What gaps were identified?",
]


def render_chat_widget(context: Dict[str, Any]):
    """
    Render the chat panel (for use inside a tab).
    Also injects a floating bubble that helps users discover the chat.
    """
    # ── Initialize state ──────────────────────────────────────────────
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    # ── Floating bubble (injected globally) ───────────────────────────
    _render_floating_bubble()

    # ── Chat section anchor (for floating bubble navigation) ──────────
    st.markdown('<div id="chat-section"></div>', unsafe_allow_html=True)

    # ── Chat panel ────────────────────────────────────────────────────
    _render_chat_panel(context)


def _render_floating_bubble():
    """Inject a floating chat bubble using an iframe component so JS works."""
    msg_count = len(st.session_state.get("chat_messages", []))
    badge_html = ""
    if msg_count > 0:
        badge_html = (
            f'<div style="position:absolute;top:-3px;right:-3px;min-width:20px;'
            f'height:20px;border-radius:10px;background:#ef4444;color:#fff;'
            f'font-size:11px;font-weight:700;display:flex;align-items:center;'
            f'justify-content:center;padding:0 4px;border:2px solid #0f172a;">'
            f'{msg_count}</div>'
        )

    bubble_html = f"""
    <div style="position:fixed;bottom:28px;right:28px;z-index:99999;">
        <a href="#chat-section" target="_parent"
           style="width:60px;height:60px;border-radius:50%;
                  background:linear-gradient(135deg,#3b82f6,#8b5cf6);
                  display:flex;align-items:center;justify-content:center;
                  text-decoration:none;cursor:pointer;position:relative;
                  box-shadow:0 4px 20px rgba(59,130,246,0.45),0 2px 8px rgba(0,0,0,0.3);
                  border:2px solid rgba(255,255,255,0.15);
                  transition:transform 0.2s;">
            <span style="font-size:1.5rem;">💬</span>
            {badge_html}
        </a>
    </div>
    """
    # Use components.html so inline styles always render correctly
    components.html(bubble_html, height=0)


def _render_chat_panel(context: Dict[str, Any]):
    """Render the chat panel with messages and input."""
    # ── Messages container (scrollable) ───────────────────────────────
    chat_container = st.container(height=420)
    with chat_container:
        if not st.session_state.chat_messages:
            # Welcome message
            st.markdown(
                """<div style="text-align:center;padding:36px 16px 12px;color:#94a3b8;">
                <div style="font-size:2.2rem;margin-bottom:10px;">🤖</div>
                <div style="font-size:1.05rem;font-weight:600;color:#e2e8f0;margin-bottom:6px;">
                    Hi! I'm your Report Assistant
                </div>
                <div style="font-size:0.86rem;line-height:1.6;">
                    I've analyzed the full research report. Ask me anything —
                    themes, claims, sources, gaps, or just <em>"give me a summary."</em>
                </div>
                </div>""",
                unsafe_allow_html=True,
            )

        for msg in st.session_state.chat_messages:
            with st.chat_message(
                msg["role"],
                avatar="🤖" if msg["role"] == "assistant" else "🧑‍💻",
            ):
                st.markdown(msg["content"])

    # ── Suggestion buttons (only when no messages yet) ────────────────
    if not st.session_state.chat_messages:
        st.markdown(
            '<div style="text-align:center;margin:12px 0 8px;font-size:0.78rem;color:#94a3b8;">Try asking:</div>',
            unsafe_allow_html=True,
        )
        scols = st.columns(len(_SUGGESTIONS))
        for idx, suggestion in enumerate(_SUGGESTIONS):
            with scols[idx]:
                if st.button(
                    suggestion,
                    key=f"chat_suggestion_{idx}",
                    use_container_width=True,
                ):
                    _send_message(suggestion, context)

    # ── Chat input ────────────────────────────────────────────────────
    if prompt := st.chat_input(
        "Ask about the research...", key="report_chat_input"
    ):
        _send_message(prompt, context)

    # ── Footer controls ───────────────────────────────────────────────
    if st.session_state.chat_messages:
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("🗑️ Clear Chat", key="chat_clear_btn", use_container_width=True):
                st.session_state.chat_messages = []
                st.rerun()


def _send_message(user_message: str, context: Dict[str, Any]):
    """Append user message, call agent, append response, rerun."""
    st.session_state.chat_messages.append(
        {"role": "user", "content": user_message}
    )
    with st.spinner("🔍 Analyzing report..."):
        response = report_chat(
            user_message=user_message,
            context=context,
            chat_history=st.session_state.chat_messages[:-1],
        )
    st.session_state.chat_messages.append(
        {"role": "assistant", "content": response}
    )
    st.rerun()
