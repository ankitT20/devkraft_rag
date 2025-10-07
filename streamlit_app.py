"""
Streamlit UI for RAG application.
Simple chatbot interface with document upload and model selection.
"""
import streamlit as st
import requests
import logging
from pathlib import Path
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("streamlit_ui")

# Configure page
st.set_page_config(
    page_title="DevKraft RAG Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

logger.info("Streamlit UI initialized")

# API endpoint
API_URL = "http://localhost:8000"

# Model configurations for display
MODEL_INFO = {
    "gemini": {
        "display": "gemini-2.5-flash: Cloud (Gemini API + Qdrant cloud)",
        "details": """
**API:** Gemini API  
**Embedding Model:** gemini-embedding-001  
**LLM Chat Model:** gemini-2.5-flash  
**Qdrant DB:** Cloud europe-west3-0.gcp.cloud.qdrant.io:6333  
**Collection:** bootcamp_rag_cloud (vector size 3072)
        """
    },
    "qwen3": {
        "display": "qwen3-1.7b: Local (LMStudio + Docker)",
        "details": """
**API:** LMStudio http://127.0.0.1:1234/ with Fallback: HF  
**Embedding Model:** text-embedding-embeddinggemma-300m-qat with Fallback: HF  
**LLM Chat Model:** qwen/qwen3-1.7b  
**Qdrant DB:** Docker http://localhost:6333/collections with Replication: qdrant.io  
**Collection:** bootcamp_rag_docker (vector size 768)
        """
    }
}


def init_session_state():
    """Initialize session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "chat_id" not in st.session_state:
        st.session_state.chat_id = None
    if "model_type" not in st.session_state:
        st.session_state.model_type = "gemini"
    if "show_thinking" not in st.session_state:
        st.session_state.show_thinking = {}


def load_chat_history(chat_id: str):
    """Load chat history from API."""
    try:
        logger.info(f"Loading chat history for chat_id: {chat_id}")
        response = requests.get(f"{API_URL}/chat/{chat_id}")
        if response.status_code == 200:
            chat_data = response.json()
            messages = chat_data.get("messages", [])
            logger.info(f"Loaded {len(messages)} messages for chat_id: {chat_id}")
            return messages
    except Exception as e:
        logger.error(f"Failed to load chat history for chat_id {chat_id}: {e}")
        st.error(f"Failed to load chat history: {e}")
    return []


def get_recent_chats():
    """Get recent chat sessions from API."""
    try:
        logger.info("Fetching recent chats from API")
        response = requests.get(f"{API_URL}/chats?limit=10")
        if response.status_code == 200:
            chats = response.json()
            logger.info(f"Retrieved {len(chats)} recent chats")
            return chats
    except Exception as e:
        logger.error(f"Failed to load recent chats: {e}")
        st.error(f"Failed to load recent chats: {e}")
    return []


def send_query(query: str, model_type: str, chat_id: str = None):
    """Send query to API."""
    try:
        logger.info(f"Sending query with model_type: {model_type}, chat_id: {chat_id}")
        payload = {
            "query": query,
            "model_type": model_type,
            "chat_id": chat_id
        }
        response = requests.post(f"{API_URL}/query", json=payload)
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Query successful, received response for chat_id: {result.get('chat_id')}")
            return result
        else:
            logger.error(f"API error: {response.status_code}")
            st.error(f"API error: {response.status_code}")
    except Exception as e:
        logger.error(f"Failed to send query: {e}")
        st.error(f"Failed to send query: {e}")
    return None


def upload_document(file):
    """Upload document to API."""
    try:
        logger.info(f"Uploading document: {file.name} (type: {file.type})")
        files = {"file": (file.name, file, file.type)}
        response = requests.post(f"{API_URL}/upload", files=files)
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Document uploaded successfully: {file.name}")
            return result
        else:
            logger.error(f"Upload error: {response.status_code}")
            st.error(f"Upload error: {response.status_code}")
    except Exception as e:
        logger.error(f"Failed to upload document {file.name}: {e}")
        st.error(f"Failed to upload document: {e}")
    return None


def main():
    """Main Streamlit application."""
    logger.info("Starting main Streamlit application")
    init_session_state()
    
    # Sidebar
    with st.sidebar:
        st.title("🤖 DevKraft RAG")
        
        # Model selection
        st.subheader("Model Selection")
        model_options = {
            "gemini": MODEL_INFO["gemini"]["display"],
            "qwen3": MODEL_INFO["qwen3"]["display"]
        }
        
        selected_display = st.selectbox(
            "Current Model:",
            options=list(model_options.values()),
            index=0 if st.session_state.model_type == "gemini" else 1
        )
        
        # Update model type based on selection
        for key, value in model_options.items():
            if value == selected_display:
                st.session_state.model_type = key
                break
        
        # Show model details in expander
        with st.expander("ℹ️ Model Details"):
            st.markdown(MODEL_INFO[st.session_state.model_type]["details"])
        
        st.markdown("---")
        
        # Document upload
        st.subheader("📄 Upload Document")
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=["txt", "pdf", "docx", "md"],
            help="Upload documents to add to the knowledge base"
        )
        
        if uploaded_file is not None:
            if st.button("➕ Upload", key="upload_btn"):
                with st.spinner("Uploading and processing..."):
                    result = upload_document(uploaded_file)
                    if result:
                        if result["success"]:
                            st.success(f"✅ {result['message']}")
                        else:
                            st.error(f"❌ {result['message']}")
        
        st.markdown("---")
        
        # Chat history
        st.subheader("💬 Recent Chats")
        
        if st.button("➕ New Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.chat_id = None
            st.rerun()
        
        if st.button("🔄 Refresh Chats"):
            st.rerun()
        
        recent_chats = get_recent_chats()
        
        if recent_chats:
            for chat in recent_chats:
                col1, col2 = st.columns([3, 1])
                with col1:
                    if st.button(
                        f"{chat['preview'][:30]}...",
                        key=f"chat_{chat['chat_id']}",
                        use_container_width=True
                    ):
                        # Load this chat
                        st.session_state.chat_id = chat['chat_id']
                        st.session_state.messages = load_chat_history(chat['chat_id'])
                        st.rerun()
                with col2:
                    st.caption(f"💬 {chat['message_count']}")
        else:
            st.info("No recent chats")
    
    # Main chat interface
    st.title(f"Welcome to Devkraft RAG - Current Model: {st.session_state.model_type.upper()}")
    
    # Display chat messages
    for i, message in enumerate(st.session_state.messages):
        role = message["role"]
        content = message["content"]
        
        with st.chat_message(role):
            st.markdown(content)
            
            # Show sources for assistant messages
            if role == "assistant" and message.get("sources"):
                with st.expander("📚 Show Sources", expanded=False):
                    for source in message["sources"]:
                        st.markdown(f"**Source {source['index']}:**")
                        st.markdown(f"- **Title/Header:** {source['title']}")
                        st.markdown(f"- **Source:** {source['source']}")
                        st.markdown(f"- **Page:** {source['page']}")
                        st.markdown(f"- **Relevance Score:** {source['score']}")
                        st.markdown("---")
            
            # Show thinking box for assistant messages in qwen3 mode
            if (role == "assistant" and 
                st.session_state.model_type == "qwen3" and 
                message.get("thinking")):
                
                thinking_key = f"thinking_{i}"
                if thinking_key not in st.session_state.show_thinking:
                    st.session_state.show_thinking[thinking_key] = False
                
                with st.expander("🧠 Show Thinking", expanded=False):
                    st.text(message["thinking"])
            
            # Add Listen button for assistant messages
            if role == "assistant":
                if st.button("🔊 Listen", key=f"listen_{i}"):
                    with st.spinner("Generating audio..."):
                        try:
                            tts_response = requests.post(
                                f"{API_URL}/tts",
                                json={"text": content}
                            )
                            if tts_response.status_code == 200:
                                st.audio(tts_response.content, format="audio/wav", autoplay=True)
                            else:
                                st.error("Failed to generate audio")
                        except Exception as e:
                            st.error(f"Audio generation error: {e}")
    
    # Chat input
    if prompt := st.chat_input("Ask a question..."):
        # Add user message to chat
        st.session_state.messages.append({
            "role": "user",
            "content": prompt,
            "timestamp": datetime.now().isoformat()
        })
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get response from API
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                result = send_query(
                    prompt, 
                    st.session_state.model_type,
                    st.session_state.chat_id
                )
                
                if result:
                    # Update chat_id
                    st.session_state.chat_id = result["chat_id"]
                    
                    # Display response
                    st.markdown(result["response"])
                    
                    # Show sources
                    if result.get("sources"):
                        with st.expander("📚 Show Sources", expanded=False):
                            for source in result["sources"]:
                                st.markdown(f"**Source {source['index']}:**")
                                st.markdown(f"- **Title/Header:** {source['title']}")
                                st.markdown(f"- **Source:** {source['source']}")
                                st.markdown(f"- **Page:** {source['page']}")
                                st.markdown(f"- **Relevance Score:** {source['score']}")
                                st.markdown("---")
                    
                    # Show thinking for qwen3
                    if result.get("thinking") and st.session_state.model_type == "qwen3":
                        with st.expander("🧠 Show Thinking", expanded=False):
                            st.text(result["thinking"])
                    
                    # Add Listen button
                    if st.button("🔊 Listen", key=f"listen_new"):
                        with st.spinner("Generating audio..."):
                            try:
                                tts_response = requests.post(
                                    f"{API_URL}/tts",
                                    json={"text": result["response"]}
                                )
                                if tts_response.status_code == 200:
                                    st.audio(tts_response.content, format="audio/wav", autoplay=True)
                                else:
                                    st.error("Failed to generate audio")
                            except Exception as e:
                                st.error(f"Audio generation error: {e}")
                    
                    # Add assistant message to chat
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": result["response"],
                        "timestamp": datetime.now().isoformat(),
                        "thinking": result.get("thinking"),
                        "sources": result.get("sources", [])
                    })
                else:
                    st.error("Failed to get response from API")


if __name__ == "__main__":
    main()
