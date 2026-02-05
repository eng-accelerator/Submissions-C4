import streamlit as st
import json
import os
from datetime import datetime
from pathlib import Path
import requests
from typing import List, Dict
import uuid
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL_NAME = "openai/gpt-oss-120b"
CHAT_DATA_DIR = Path("./chat_data")
CHAT_DATA_DIR.mkdir(exist_ok=True)

# Validate API key
if not OPENROUTER_API_KEY:
    st.error("⚠️ OPENROUTER_API_KEY not found in environment variables!")
    st.info("Please create a .env file with your OpenRouter API key")
    st.code("OPENROUTER_API_KEY=your-key-here")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="ChatGPT Clone",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)


def apply_theme(dark_mode: bool):
    """Apply dark or light theme"""
    if dark_mode:
        st.markdown("""
        <style>
            .stApp {
                background-color: #212121;
                color: #ffffff;
            }
            .chat-message {
                padding: 1rem;
                border-radius: 0.5rem;
                margin-bottom: 1rem;
            }
            .user-message {
                background-color: #2d2d2d;
            }
            .assistant-message {
                background-color: #1a1a1a;
            }
            .stButton>button {
                width: 100%;
            }
            .chat-title {
                font-size: 1.5rem;
                font-weight: bold;
                margin-bottom: 1rem;
                color: #ffffff;
            }
            .stMarkdown {
                color: #ffffff;
            }
            /* Custom avatar styles */
            [data-testid="stChatMessageAvatarUser"] {
                background-color: #ef4444 !important;
            }
            [data-testid="stChatMessageAvatarAssistant"] {
                background-color: #f97316 !important;
            }
            /* Token counter styles */
            .token-counter {
                background-color: #2d2d2d;
                padding: 0.5rem 1rem;
                border-radius: 0.5rem;
                font-size: 0.9rem;
                color: #10b981;
                font-weight: bold;
                border: 1px solid #374151;
            }
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <style>
            .stApp {
                background-color: #ffffff;
                color: #000000;
            }
            .chat-message {
                padding: 1rem;
                border-radius: 0.5rem;
                margin-bottom: 1rem;
            }
            .user-message {
                background-color: #f0f0f0;
            }
            .assistant-message {
                background-color: #e8e8e8;
            }
            .stButton>button {
                width: 100%;
            }
            .chat-title {
                font-size: 1.5rem;
                font-weight: bold;
                margin-bottom: 1rem;
                color: #000000;
            }
            .stMarkdown {
                color: #000000;
            }
            /* Custom avatar styles */
            [data-testid="stChatMessageAvatarUser"] {
                background-color: #ef4444 !important;
            }
            [data-testid="stChatMessageAvatarAssistant"] {
                background-color: #f97316 !important;
            }
            /* Token counter styles */
            .token-counter {
                background-color: #f0f0f0;
                padding: 0.5rem 1rem;
                border-radius: 0.5rem;
                font-size: 0.9rem;
                color: #059669;
                font-weight: bold;
                border: 1px solid #d1d5db;
            }
        </style>
        """, unsafe_allow_html=True)


class ChatManager:
    """Manages chat operations and local storage"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.chats_index_file = data_dir / "chats_index.json"
        self._ensure_index_exists()
    
    def _ensure_index_exists(self):
        """Create index file if it doesn't exist"""
        if not self.chats_index_file.exists():
            self._save_index([])
    
    def _load_index(self) -> List[Dict]:
        """Load chats index from file"""
        with open(self.chats_index_file, 'r') as f:
            return json.load(f)
    
    def _save_index(self, index: List[Dict]):
        """Save chats index to file"""
        with open(self.chats_index_file, 'w') as f:
            json.dump(index, f, indent=2)
    
    def create_chat(self) -> str:
        """Create a new chat and return its ID"""
        chat_id = str(uuid.uuid4())
        timestamp = datetime.now()
        
        chat_data = {
            "id": chat_id,
            "title": "Empty Chat",
            "created_at": timestamp.isoformat(),
            "updated_at": timestamp.isoformat(),
            "messages": [],
            "summary": None,
            "title_generated": False,
            "total_tokens": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0
        }
        
        # Save chat file
        chat_file = self.data_dir / f"{chat_id}.json"
        with open(chat_file, 'w') as f:
            json.dump(chat_data, f, indent=2)
        
        # Update index
        index = self._load_index()
        index.append({
            "id": chat_id,
            "title": "Empty Chat",
            "created_at": timestamp.isoformat(),
            "updated_at": timestamp.isoformat()
        })
        self._save_index(index)
        
        return chat_id
    
    def get_all_chats(self) -> List[Dict]:
        """Get all chats from index"""
        return self._load_index()
    
    def load_chat(self, chat_id: str) -> Dict:
        """Load a specific chat"""
        chat_file = self.data_dir / f"{chat_id}.json"
        if chat_file.exists():
            with open(chat_file, 'r') as f:
                return json.load(f)
        return None
    
    def save_chat(self, chat_data: Dict):
        """Save chat data"""
        chat_id = chat_data["id"]
        chat_data["updated_at"] = datetime.now().isoformat()
        
        # Save chat file
        chat_file = self.data_dir / f"{chat_id}.json"
        with open(chat_file, 'w') as f:
            json.dump(chat_data, f, indent=2)
        
        # Update index
        index = self._load_index()
        for i, chat in enumerate(index):
            if chat["id"] == chat_id:
                index[i]["title"] = chat_data["title"]
                index[i]["updated_at"] = chat_data["updated_at"]
                break
        self._save_index(index)
    
    def delete_chat(self, chat_id: str):
        """Delete a chat"""
        # Remove from index
        index = self._load_index()
        index = [chat for chat in index if chat["id"] != chat_id]
        self._save_index(index)
        
        # Delete chat file
        chat_file = self.data_dir / f"{chat_id}.json"
        if chat_file.exists():
            chat_file.unlink()
    
    def clear_chat(self, chat_id: str):
        """Clear all messages from a chat"""
        chat_data = self.load_chat(chat_id)
        if chat_data:
            chat_data["messages"] = []
            chat_data["summary"] = None
            chat_data["title_generated"] = False
            chat_data["title"] = "Empty Chat"
            chat_data["total_tokens"] = 0
            chat_data["prompt_tokens"] = 0
            chat_data["completion_tokens"] = 0
            self.save_chat(chat_data)


class OpenRouterClient:
    """Client for OpenRouter API"""
    
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
    
    def chat(self, messages: List[Dict], temperature: float = 0.7, max_tokens: int = 2000) -> tuple:
        """Send chat request to OpenRouter and return response with token usage"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8501",
            "X-Title": "Streamlit ChatGPT Clone"
        }
        
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        try:
            response = requests.post(self.base_url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            # Extract token usage
            usage = result.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", 0)
            
            content = result["choices"][0]["message"]["content"]
            
            return content, prompt_tokens, completion_tokens, total_tokens
        except Exception as e:
            return f"Error: {str(e)}", 0, 0, 0
    
    def generate_summary(self, messages: List[Dict]) -> str:
        """Generate a summary of the conversation"""
        summary_prompt = [
            {"role": "system", "content": "You are a helpful assistant that summarizes conversations concisely in 2-3 sentences."},
            {"role": "user", "content": f"Summarize this conversation:\n\n{json.dumps(messages, indent=2)}"}
        ]
        response, _, _, _ = self.chat(summary_prompt, temperature=0.3, max_tokens=150)
        return response


def initialize_session_state():
    """Initialize Streamlit session state"""
    if "chat_manager" not in st.session_state:
        st.session_state.chat_manager = ChatManager(CHAT_DATA_DIR)
    
    if "openrouter_client" not in st.session_state:
        st.session_state.openrouter_client = OpenRouterClient(OPENROUTER_API_KEY, MODEL_NAME)
    
    if "current_chat_id" not in st.session_state:
        chats = st.session_state.chat_manager.get_all_chats()
        if not chats:
            st.session_state.current_chat_id = st.session_state.chat_manager.create_chat()
        else:
            st.session_state.current_chat_id = chats[0]["id"]
    
    if "generating" not in st.session_state:
        st.session_state.generating = False
    
    if "dark_mode" not in st.session_state:
        st.session_state.dark_mode = True


def update_chat_title(chat_data: Dict):
    """Auto-generate chat title from first user message"""
    if not chat_data.get("title_generated", False) and len(chat_data["messages"]) >= 1:
        # Get first user message
        first_user_msg = next((msg for msg in chat_data["messages"] if msg["role"] == "user"), None)
        if first_user_msg:
            # Use first user message as title
            title = first_user_msg["content"].strip()
            
            # Limit to 40 characters for sidebar display
            if len(title) > 40:
                title = title[:40] + "..."
            
            chat_data["title"] = title
            chat_data["title_generated"] = True


def render_sidebar():
    """Render the sidebar with chat history"""
    with st.sidebar:
        st.title("💬 Conversations")
        
        # New Chat button
        if st.button("➕ New Chat", use_container_width=True, type="primary"):
            new_chat_id = st.session_state.chat_manager.create_chat()
            st.session_state.current_chat_id = new_chat_id
            st.rerun()
        
        st.divider()
        st.subheader("Chat History")
        
        # Get all chats
        chats = st.session_state.chat_manager.get_all_chats()
        
        # Sort by updated_at (most recent first)
        chats.sort(key=lambda x: x["updated_at"], reverse=True)
        
        # Display chats
        for chat in chats:
            col1, col2 = st.columns([4, 1])
            
            with col1:
                is_current = chat["id"] == st.session_state.current_chat_id
                # Load full chat data to get actual title
                full_chat = st.session_state.chat_manager.load_chat(chat["id"])
                if full_chat:
                    chat_title = full_chat.get("title", "Empty Chat")
                else:
                    chat_title = chat.get("title", "Empty Chat")
                
                # Ensure title is not empty
                if not chat_title or chat_title.strip() == "":
                    chat_title = "Empty Chat"
                
                if st.button(
                    chat_title,
                    key=f"chat_{chat['id']}",
                    use_container_width=True,
                    type="secondary" if is_current else "tertiary"
                ):
                    st.session_state.current_chat_id = chat["id"]
                    st.rerun()
            
            with col2:
                if st.button("🗑️", key=f"delete_{chat['id']}", help="Delete chat"):
                    st.session_state.chat_manager.delete_chat(chat["id"])
                    if chat["id"] == st.session_state.current_chat_id:
                        remaining_chats = st.session_state.chat_manager.get_all_chats()
                        if remaining_chats:
                            st.session_state.current_chat_id = remaining_chats[0]["id"]
                        else:
                            st.session_state.current_chat_id = st.session_state.chat_manager.create_chat()
                    st.rerun()
        
        st.divider()
        
        # Settings
        st.subheader("⚙️ Settings")
        
        # Theme toggle
        dark_mode = st.toggle("🌙 Dark Mode", value=st.session_state.dark_mode)
        if dark_mode != st.session_state.dark_mode:
            st.session_state.dark_mode = dark_mode
            st.rerun()
        
        if st.button("🗑️ Clear Current Chat", use_container_width=True):
            st.session_state.chat_manager.clear_chat(st.session_state.current_chat_id)
            st.rerun()


def render_chat():
    """Render the main chat interface"""
    chat_data = st.session_state.chat_manager.load_chat(st.session_state.current_chat_id)
    
    if not chat_data:
        st.error("Chat not found!")
        return
    
    # Ensure token fields exist (for backward compatibility)
    if "total_tokens" not in chat_data:
        chat_data["total_tokens"] = 0
        chat_data["prompt_tokens"] = 0
        chat_data["completion_tokens"] = 0
    
    # Top bar with title and token counter
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown(f'<div class="chat-title">💬 {chat_data["title"]}</div>', unsafe_allow_html=True)
    
    with col2:
        total_tokens = chat_data.get("total_tokens", 0)
        prompt_tokens = chat_data.get("prompt_tokens", 0)
        completion_tokens = chat_data.get("completion_tokens", 0)
        
        st.markdown(f"""
        <div class="token-counter">
            🎯 Tokens: {total_tokens:,}<br>
            📥 Input: {prompt_tokens:,}<br>
            📤 Output: {completion_tokens:,}
        </div>
        """, unsafe_allow_html=True)
    
    # Summary expander (if chat has messages)
    if chat_data["messages"]:
        with st.expander("📝 Summarize Conversation"):
            if st.button("Generate Summary", use_container_width=True):
                with st.spinner("Generating summary..."):
                    summary = st.session_state.openrouter_client.generate_summary(chat_data["messages"])
                    chat_data["summary"] = summary
                    st.session_state.chat_manager.save_chat(chat_data)
                    st.rerun()
            
            if chat_data.get("summary"):
                st.info(chat_data["summary"])
    
    # Display messages
    for message in chat_data["messages"]:
        role = message["role"]
        content = message["content"]
        
        if role == "user":
            with st.chat_message("user", avatar="😊"):
                st.markdown(content)
        else:
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown(content)
    
    # Chat input
    if prompt := st.chat_input("What would you like to know?"):
        # Add user message to chat
        chat_data["messages"].append({"role": "user", "content": prompt})
        
        # Auto-generate title from first message
        update_chat_title(chat_data)
        
        # Save chat
        st.session_state.chat_manager.save_chat(chat_data)
        
        # Display user message
        with st.chat_message("user", avatar="😊"):
            st.markdown(prompt)
        
        # Generate assistant response
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Thinking..."):
                response, prompt_tok, completion_tok, total_tok = st.session_state.openrouter_client.chat(chat_data["messages"])
                st.markdown(response)
        
        # Add assistant message to chat
        chat_data["messages"].append({"role": "assistant", "content": response})
        
        # Update token counts
        chat_data["prompt_tokens"] = chat_data.get("prompt_tokens", 0) + prompt_tok
        chat_data["completion_tokens"] = chat_data.get("completion_tokens", 0) + completion_tok
        chat_data["total_tokens"] = chat_data.get("total_tokens", 0) + total_tok
        
        # Save chat
        st.session_state.chat_manager.save_chat(chat_data)
        
        st.rerun()


def main():
    """Main application"""
    initialize_session_state()
    
    # Apply theme
    apply_theme(st.session_state.dark_mode)
    
    render_sidebar()
    render_chat()


if __name__ == "__main__":
    main()
