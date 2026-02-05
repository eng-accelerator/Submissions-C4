import streamlit as st
import datetime
import json
import os
import uuid
from pathlib import Path
from typing import List, Dict, Optional
import requests
import toml
import logging

# ============================================================================
# Logging Configuration
# ============================================================================
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('chat_app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# Configuration
# ============================================================================
APP_TITLE = "Streamlit Chat App"
CHAT_HISTORY_DIR = Path("chat_history")
CHAT_HISTORY_DIR.mkdir(exist_ok=True)

# OpenRouter API config - HARDCODED MODEL
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "openai/gpt-oss-120b"  # Hardcoded model

# ============================================================================
# Session State Initialization
# ============================================================================
def init_session_state():
    """Initialize all session state variables."""
    logger.debug("Initializing session state...")
    
    if 'conversations' not in st.session_state:
        st.session_state.conversations = {}
        logger.debug("Initialized conversations dict")
    
    if 'current_chat_id' not in st.session_state:
        st.session_state.current_chat_id = None
        logger.debug("Initialized current_chat_id")
    
    if 'message_input' not in st.session_state:
        st.session_state.message_input = ''
        logger.debug("Initialized message_input")
    
    # Load API key from secrets.toml only
    if 'openrouter_key' not in st.session_state:
        logger.debug("API key not in session state, loading from secrets.toml...")
        api_key = get_openrouter_key_from_file()
        st.session_state.openrouter_key = api_key if api_key else ""
        logger.info(f"API key loaded: {'Yes' if api_key else 'No'} (length: {len(st.session_state.openrouter_key) if st.session_state.openrouter_key else 0})")
    
    # Hardcoded model
    if 'model' not in st.session_state:
        st.session_state.model = DEFAULT_MODEL
        logger.debug(f"Initialized model: {st.session_state.model}")
    
    # Model settings (configurable from UI)
    if 'temperature' not in st.session_state:
        st.session_state.temperature = 0.7
    if 'max_tokens' not in st.session_state:
        st.session_state.max_tokens = 1024
    if 'top_p' not in st.session_state:
        st.session_state.top_p = 1.0
    if 'frequency_penalty' not in st.session_state:
        st.session_state.frequency_penalty = 0.0
    if 'presence_penalty' not in st.session_state:
        st.session_state.presence_penalty = 0.0
    
    if 'assistant_name' not in st.session_state:
        st.session_state.assistant_name = 'AI Assistant'
    
    if 'show_timestamps' not in st.session_state:
        st.session_state.show_timestamps = False
    
    if 'session_start' not in st.session_state:
        st.session_state.session_start = datetime.datetime.utcnow()
    
    # Theme state
    if 'theme' not in st.session_state:
        st.session_state.theme = 'light'
        logger.debug("Initialized theme to light")

# ============================================================================
# File I/O Functions
# ============================================================================
def get_openrouter_key_from_file():
    """Read OpenRouter API key directly from secrets.toml file."""
    secrets_path = Path(".streamlit/secrets.toml")
    
    logger.debug(f"Looking for secrets file at: {secrets_path.absolute()}")
    
    if not secrets_path.exists():
        logger.error(f"Secrets file not found at {secrets_path.absolute()}")
        st.error(f"⚠️ Secrets file not found at `.streamlit/secrets.toml`. Please create it with your API key.")
        return None
    
    try:
        logger.debug(f"Reading secrets from {secrets_path}")
        secrets = toml.load(secrets_path)
        
        logger.debug(f"Secrets file keys: {list(secrets.keys())}")
        
        api_key = secrets.get("openrouter_key")
        
        if api_key:
            safe_key = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "***"
            logger.info(f"API key found in secrets file: {safe_key} (length: {len(api_key)})")
        else:
            logger.warning("'openrouter_key' not found in secrets.toml")
            st.error("⚠️ 'openrouter_key' not found in `.streamlit/secrets.toml`")
        
        return api_key
    except Exception as e:
        logger.error(f"Error reading secrets file: {e}", exc_info=True)
        st.error(f"❌ Error reading secrets file: {e}")
        return None

def generate_chat_id() -> str:
    """Generate a unique chat ID with timestamp."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_suffix = str(uuid.uuid4())[:8]
    chat_id = f"{timestamp}_{unique_suffix}"
    logger.debug(f"Generated chat_id: {chat_id}")
    return chat_id

def save_chat_to_file(chat_data: Dict) -> str:
    """Save chat to JSON file in chat_history folder."""
    chat_id = chat_data.get('chat_id')
    filename = CHAT_HISTORY_DIR / f"{chat_id}.json"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(chat_data, f, indent=2, ensure_ascii=False)
        logger.debug(f"Saved chat to {filename}")
        return str(filename)
    except Exception as e:
        logger.error(f"Error saving chat to file: {e}", exc_info=True)
        raise

def load_chat_from_file(chat_id: str) -> Optional[Dict]:
    """Load chat from JSON file."""
    filename = CHAT_HISTORY_DIR / f"{chat_id}.json"
    
    if filename.exists():
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                chat_data = json.load(f)
            logger.debug(f"Loaded chat {chat_id} from file")
            return chat_data
        except Exception as e:
            logger.error(f"Error loading chat from file: {e}", exc_info=True)
            return None
    else:
        logger.warning(f"Chat file not found: {filename}")
        return None

def list_chats() -> List[Dict]:
    """List all chats from chat_history folder."""
    chats = []
    if CHAT_HISTORY_DIR.exists():
        for file in sorted(CHAT_HISTORY_DIR.glob("*.json"), reverse=True):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    chat_data = json.load(f)
                    chats.append(chat_data)
            except Exception as e:
                logger.warning(f"Failed to load {file.name}: {e}")
    
    logger.debug(f"Listed {len(chats)} chats")
    return chats

def delete_chat_file(chat_id: str):
    """Delete chat file."""
    filename = CHAT_HISTORY_DIR / f"{chat_id}.json"
    if filename.exists():
        try:
            filename.unlink()
            logger.info(f"Deleted chat file: {chat_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting chat file: {e}", exc_info=True)
            return False
    else:
        logger.warning(f"Chat file not found for deletion: {chat_id}")
        return False

def create_new_chat(title: str = "New Chat") -> Dict:
    """Create a new chat session."""
    logger.info(f"Creating new chat: {title}")
    
    chat_id = generate_chat_id()
    now = datetime.datetime.utcnow().isoformat()
    chat_data = {
        "chat_id": chat_id,
        "title": title,
        "messages": [],
        "created_at": now,
        "updated_at": now
    }
    
    save_chat_to_file(chat_data)
    st.session_state.conversations[chat_id] = chat_data
    st.session_state.current_chat_id = chat_id
    
    logger.info(f"Created new chat with ID: {chat_id}")
    return chat_data

def load_all_chats():
    """Load all chats into session state."""
    logger.debug("Loading all chats into session state...")
    count = 0
    
    for chat_data in list_chats():
        chat_id = chat_data.get('chat_id')
        if chat_id:
            st.session_state.conversations[chat_id] = chat_data
            count += 1
    
    logger.info(f"Loaded {count} chats into session state")

# ============================================================================
# Message Functions
# ============================================================================
def add_message(chat_id: str, role: str, message: str):
    """Add a message to a chat and save to file."""
    logger.debug(f"Adding {role} message to chat {chat_id}")
    
    if chat_id not in st.session_state.conversations:
        logger.error(f"Chat {chat_id} not found in session state")
        return
    
    chat_data = st.session_state.conversations[chat_id]
    chat_data['messages'].append({
        'role': role,
        'message': message
    })
    chat_data['updated_at'] = datetime.datetime.utcnow().isoformat()
    
    save_chat_to_file(chat_data)
    logger.info(f"Added {role} message to chat {chat_id} (total messages: {len(chat_data['messages'])})")

def get_messages_for_api(chat_id: str) -> List[Dict]:
    """Convert messages to OpenRouter API format."""
    if chat_id not in st.session_state.conversations:
        logger.warning(f"Chat {chat_id} not found for API message conversion")
        return []
    
    chat_data = st.session_state.conversations[chat_id]
    api_messages = []
    
    for msg in chat_data.get('messages', []):
        api_messages.append({
            'role': msg.get('role'),
            'content': msg.get('message')
        })
    
    logger.debug(f"Converted {len(api_messages)} messages for API")
    return api_messages

def call_openrouter(
    messages: List[Dict], 
    model: str, 
    temperature: float, 
    api_key: str,
    max_tokens: int = 1024,
    top_p: float = 1.0,
    frequency_penalty: float = 0.0,
    presence_penalty: float = 0.0
) -> str:
    """Call OpenRouter API."""
    logger.info(f"Calling OpenRouter API with model: {model}, temperature: {temperature}")
    logger.debug(f"API key present: {bool(api_key)}, length: {len(api_key) if api_key else 0}")
    logger.debug(f"Number of messages: {len(messages)}")
    
    if not api_key or api_key.strip() == "":
        error_msg = "OpenRouter API key is not set or empty"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8501",
        "X-Title": "Streamlit Chat App"
    }
    
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "top_p": top_p,
        "frequency_penalty": frequency_penalty,
        "presence_penalty": presence_penalty
    }
    
    logger.debug(f"Request payload: {payload}")
    
    try:
        response = requests.post(
            OPENROUTER_BASE_URL, 
            json=payload, 
            headers=headers, 
            timeout=60
        )
        
        logger.debug(f"API response status code: {response.status_code}")
        
        response.raise_for_status()
        result = response.json()
        
        logger.debug(f"API response keys: {list(result.keys())}")
        
        assistant_message = result['choices'][0]['message']['content']
        logger.info(f"API call successful, response length: {len(assistant_message)}")
        
        return assistant_message
        
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error from OpenRouter: {e}", exc_info=True)
        logger.error(f"Response content: {e.response.text if hasattr(e, 'response') else 'N/A'}")
        raise RuntimeError(f"OpenRouter API HTTP error: {e}")
    except requests.exceptions.Timeout:
        logger.error("Request to OpenRouter timed out")
        raise RuntimeError("OpenRouter API request timed out")
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {e}", exc_info=True)
        raise RuntimeError(f"OpenRouter API error: {e}")
    except KeyError as e:
        logger.error(f"Unexpected response format from API: {e}", exc_info=True)
        logger.error(f"Response content: {result if 'result' in locals() else 'N/A'}")
        raise RuntimeError(f"Unexpected API response format: {e}")
    except Exception as e:
        logger.error(f"Unexpected error calling OpenRouter: {e}", exc_info=True)
        raise RuntimeError(f"Unexpected error: {e}")

# ============================================================================
# UI Functions
# ============================================================================
def render_message(role: str, message: str, timestamp: Optional[str] = None):
    """Render a single message."""
    if role == 'user':
        st.markdown(f"**You:** {message}")
    else:
        st.markdown(f"**{st.session_state.assistant_name}:** {message}")
    if timestamp and st.session_state.show_timestamps:
        st.caption(timestamp)

def get_chat_preview(chat_data: Dict) -> str:
    """Generate a concise chat preview for selectbox."""
    title = chat_data.get('title', 'Untitled')
    created_at = chat_data.get('created_at', '')
    messages = chat_data.get('messages', [])
    
    # Format: "Title (3 msgs) - 2024-01-15"
    date_str = created_at[:10] if created_at else "Unknown"
    msg_count = len(messages)
    
    return f"{title} ({msg_count} msg{'s' if msg_count != 1 else ''}) - {date_str}"

def toggle_theme():
    """Toggle between light and dark theme."""
    if st.session_state.theme == 'light':
        st.session_state.theme = 'dark'
        logger.info("Switched to dark theme")
    else:
        st.session_state.theme = 'light'
        logger.info("Switched to light theme")

def apply_theme():
    """Apply custom CSS based on current theme."""
    if st.session_state.theme == 'dark':
        css = """
        <style>
            .stApp {
                background-color: #0e1117;
                color: #fafafa;
            }
            .stTextInput > div > div > input {
                background-color: #262730;
                color: #fafafa;
            }
            .stTextArea > div > div > textarea {
                background-color: #262730;
                color: #fafafa;
            }
            .stSelectbox > div > div > select {
                background-color: #262730;
                color: #fafafa;
            }
            .stButton > button {
                background-color: #262730;
                color: #fafafa;
            }
            .stMarkdown {
                color: #fafafa;
            }
        </style>
        """
    else:
        css = """
        <style>
            .stApp {
                background-color: #ffffff;
                color: #31333f;
            }
            .stTextInput > div > div > input {
                background-color: #f0f2f6;
                color: #31333f;
            }
            .stTextArea > div > div > textarea {
                background-color: #f0f2f6;
                color: #31333f;
            }
            .stSelectbox > div > div > select {
                background-color: #f0f2f6;
                color: #31333f;
            }
            .stButton > button {
                background-color: #f0f2f6;
                color: #31333f;
            }
            .stMarkdown {
                color: #31333f;
            }
        </style>
        """
    st.markdown(css, unsafe_allow_html=True)


def main():
    logger.info("=" * 80)
    logger.info("Starting Streamlit Chat App")
    logger.info("=" * 80)
    
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    init_session_state()
    load_all_chats()
    
    # Apply theme
    apply_theme()
    
    st.title(f"🚀 {APP_TITLE}")
    
    # ========================================================================
    # SIDEBAR: Chat Selection & Settings
    # ========================================================================
    with st.sidebar:
        # Theme toggle button at the top
        col1, col2 = st.columns([3, 1])
        with col1:
            st.header("💬 Chats")
        with col2:
            theme_icon = "🌙" if st.session_state.theme == 'light' else "☀️"
            if st.button(theme_icon, help="Toggle theme"):
                toggle_theme()
                st.rerun()
        
        # Create new chat
        new_chat_title = st.text_input(
            "New Chat Title", 
            placeholder="e.g., My Question", 
            key="new_chat_title"
        )
        if st.button("➕ Create New Chat", use_container_width=True):
            create_new_chat(new_chat_title or "New Chat")
            st.rerun()
        
        st.markdown("---")
        
        # Chat selection using selectbox (more concise)
        all_chats = list_chats()
        if all_chats:
            # Create options for selectbox
            chat_options = {
                get_chat_preview(chat): chat.get('chat_id') 
                for chat in all_chats
            }
            
            # Get current selection index
            current_index = 0
            if st.session_state.current_chat_id:
                for idx, chat in enumerate(all_chats):
                    if chat.get('chat_id') == st.session_state.current_chat_id:
                        current_index = idx
                        break
            
            selected_preview = st.selectbox(
                "Select Chat",
                options=list(chat_options.keys()),
                index=current_index,
                key="chat_selector"
            )
            
            # Update current chat if selection changed
            selected_chat_id = chat_options[selected_preview]
            if selected_chat_id != st.session_state.current_chat_id:
                st.session_state.current_chat_id = selected_chat_id
                logger.info(f"Selected chat: {selected_chat_id}")
                st.rerun()
            
            # Action buttons for selected chat
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ Delete", use_container_width=True, help="Delete selected chat"):
                    delete_chat_file(st.session_state.current_chat_id)
                    st.session_state.current_chat_id = None
                    st.rerun()
            
            with col2:
                if st.button("🔄 Clear", use_container_width=True, help="Clear messages"):
                    if st.session_state.current_chat_id in st.session_state.conversations:
                        st.session_state.conversations[st.session_state.current_chat_id]['messages'] = []
                        st.session_state.conversations[st.session_state.current_chat_id]['updated_at'] = datetime.datetime.utcnow().isoformat()
                        save_chat_to_file(st.session_state.conversations[st.session_state.current_chat_id])
                        logger.info(f"Cleared messages for chat: {st.session_state.current_chat_id}")
                    st.rerun()
        else:
            st.info("No chats yet. Create one to get started!")
        
        st.markdown("---")
        
        # Model Settings
        st.header("⚙️ Model Settings")
        
        # Show current model (read-only)
        st.info(f"**Model:** {st.session_state.model}")
        
        # Configurable model parameters
        st.session_state.temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=2.0,
            value=st.session_state.temperature,
            step=0.1,
            help="Controls randomness. Lower = more focused, Higher = more creative"
        )
        
        st.session_state.max_tokens = st.slider(
            "Max Tokens",
            min_value=256,
            max_value=4096,
            value=st.session_state.max_tokens,
            step=256,
            help="Maximum length of the response"
        )
        
        st.session_state.top_p = st.slider(
            "Top P",
            min_value=0.0,
            max_value=1.0,
            value=st.session_state.top_p,
            step=0.05,
            help="Nucleus sampling threshold"
        )
        
        with st.expander("Advanced Settings"):
            st.session_state.frequency_penalty = st.slider(
                "Frequency Penalty",
                min_value=0.0,
                max_value=2.0,
                value=st.session_state.frequency_penalty,
                step=0.1,
                help="Reduces repetition of tokens"
            )
            
            st.session_state.presence_penalty = st.slider(
                "Presence Penalty",
                min_value=0.0,
                max_value=2.0,
                value=st.session_state.presence_penalty,
                step=0.1,
                help="Encourages discussing new topics"
            )
        
        st.markdown("---")
        
        # Assistant Settings
        st.header("🤖 Assistant Settings")
        st.session_state.assistant_name = st.text_input(
            "Assistant Name", 
            value=st.session_state.assistant_name
        )
        st.session_state.show_timestamps = st.checkbox(
            "Show Timestamps", 
            value=st.session_state.show_timestamps
        )
        
        st.markdown("---")
        
        # API Key Status (read-only)
        st.header("🔑 API Status")
        if st.session_state.openrouter_key:
            safe_key = f"{st.session_state.openrouter_key[:8]}...{st.session_state.openrouter_key[-4:]}"
            st.success(f"✅ Key Loaded: {safe_key}")
        else:
            st.error("❌ No API key found in `.streamlit/secrets.toml`")
        
        st.markdown("---")
        st.caption(f"Session: {st.session_state.session_start.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # ========================================================================
    # MAIN CHAT AREA
    # ========================================================================
    if st.session_state.current_chat_id is None:
        st.info("👈 Select a chat from the sidebar or create a new one to get started!")
        return
    
    chat_id = st.session_state.current_chat_id
    if chat_id not in st.session_state.conversations:
        logger.error(f"Chat {chat_id} not found in conversations")
        st.error("Chat not found!")
        return
    
    chat_data = st.session_state.conversations[chat_id]
    
    # Display chat title and metadata
    col1, col2 = st.columns([3, 1])
    with col1:
        st.header(f"📝 {chat_data.get('title', 'Untitled')}")
    with col2:
        st.caption(f"Created: {chat_data.get('created_at', 'N/A')[:10]}")
    
    st.divider()
    
    # Display messages
    messages = chat_data.get('messages', [])
    if not messages:
        st.info("No messages yet. Start the conversation!")
    else:
        for msg in messages:
            role = msg.get('role')
            message = msg.get('message')
            with st.container():
                render_message(role, message)
                st.divider()
    
    # Message input form
    with st.form("message_form", clear_on_submit=True):
        user_input = st.text_area(
            "Your Message", 
            height=100, 
            placeholder="Type your message here..."
        )
        
        logger.debug(f"Form - API key present: {bool(st.session_state.openrouter_key)}")
        
        col1, col2 = st.columns([4, 1])
        with col1:
            submit = st.form_submit_button("📤 Send", use_container_width=True)
        
        if submit and user_input.strip():
            logger.info(f"User submitted message (length: {len(user_input)})")
            
            if not st.session_state.openrouter_key or st.session_state.openrouter_key.strip() == "":
                logger.error("Attempted to send message without API key")
                st.error("❌ Error: OpenRouter API key not found. Please add it to `.streamlit/secrets.toml`")
                return
            
            # Add user message
            add_message(chat_id, "user", user_input.strip())
            
            # Get API response
            try:
                with st.spinner("🤖 AI is thinking..."):
                    api_messages = get_messages_for_api(chat_id)
                    
                    logger.info(f"Calling API with {len(api_messages)} messages")
                    
                    assistant_reply = call_openrouter(
                        messages=api_messages,
                        model=st.session_state.model,
                        temperature=st.session_state.temperature,
                        api_key=st.session_state.openrouter_key,
                        max_tokens=st.session_state.max_tokens,
                        top_p=st.session_state.top_p,
                        frequency_penalty=st.session_state.frequency_penalty,
                        presence_penalty=st.session_state.presence_penalty
                    )
                    
                    add_message(chat_id, "assistant", assistant_reply)
                    st.session_state.conversations[chat_id] = load_chat_from_file(chat_id)
                    
                    logger.info("Message exchange completed successfully")
                
                st.rerun()
                
            except ValueError as e:
                logger.error(f"Validation error: {e}")
                st.error(f"❌ Configuration Error: {e}")
            except RuntimeError as e:
                logger.error(f"Runtime error: {e}")
                st.error(f"❌ API Error: {e}")
            except Exception as e:
                logger.error(f"Unexpected error: {e}", exc_info=True)
                st.error(f"❌ Unexpected Error: {e}")


if __name__ == '__main__':
    main()