"""
MongoDB chat storage service with JSON file fallback.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

from pymongo import MongoClient, DESCENDING
from pymongo.server_api import ServerApi
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from app.config import settings
from app.utils.logging_config import app_logger, error_logger


class ChatStorageService:
    """
    Service for storing and retrieving chat history from MongoDB Atlas.
    Falls back to JSON files if MongoDB is unavailable.
    """
    
    def __init__(self):
        """Initialize MongoDB client with fallback to JSON files."""
        self.mongo_available = False
        self.client = None
        self.db = None
        self.collection = None
        
        # Ensure user_chat folder exists for fallback
        Path(settings.user_chat_folder).mkdir(parents=True, exist_ok=True)
        
        # Try to connect to MongoDB
        if settings.mongo_uri:
            try:
                # Append required parameters to URI
                mongo_uri = self._build_mongo_uri(settings.mongo_uri)
                
                # Create MongoDB client
                self.client = MongoClient(
                    mongo_uri,
                    server_api=ServerApi('1'),
                    serverSelectionTimeoutMS=5000  # 5 second timeout
                )
                
                # Test connection
                self.client.admin.command('ping')
                
                # Initialize database and collection
                self.db = self.client[settings.mongo_db_name]
                self.collection = self.db[settings.mongo_collection_name]
                
                # Create indexes for better query performance
                self.collection.create_index("chat_id", unique=True)
                self.collection.create_index([("updated_at", DESCENDING)])
                
                self.mongo_available = True
                app_logger.info("Successfully connected to MongoDB Atlas")
                
            except (ConnectionFailure, ServerSelectionTimeoutError) as e:
                app_logger.warning(f"MongoDB connection failed, using JSON file fallback: {e}")
                self.mongo_available = False
            except Exception as e:
                error_logger.error(f"Unexpected error connecting to MongoDB: {e}")
                self.mongo_available = False
        else:
            app_logger.warning("MONGO_URI not configured, using JSON file fallback")
    
    def _build_mongo_uri(self, base_uri: str) -> str:
        """
        Build complete MongoDB URI with required parameters.
        
        Args:
            base_uri: Base MongoDB URI from environment
            
        Returns:
            Complete MongoDB URI
        """
        # Check if URI already has the required parameters
        if "&w=majority" in base_uri and "&appName=ragcluster" in base_uri:
            return base_uri
        
        # Append required parameters
        separator = "&" if "?" in base_uri else "?"
        return f"{base_uri}{separator}w=majority&appName=ragcluster"
    
    def save_chat_history(self, chat_id: str, messages: List[Dict], model_type: str) -> bool:
        """
        Save chat history to MongoDB or JSON file as fallback.
        
        Args:
            chat_id: Chat session ID
            messages: List of chat messages
            model_type: Model type used
            
        Returns:
            True if saved successfully
        """
        data = {
            "chat_id": chat_id,
            "model_type": model_type,
            "created_at": messages[0]["timestamp"] if messages else datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "messages": messages
        }
        
        # Try MongoDB first
        if self.mongo_available:
            try:
                self.collection.replace_one(
                    {"chat_id": chat_id},
                    data,
                    upsert=True
                )
                app_logger.info(f"Saved chat history to MongoDB for chat_id={chat_id}")
                return True
            except Exception as e:
                error_logger.error(f"Failed to save to MongoDB for chat_id={chat_id}: {e}")
                app_logger.info("Falling back to JSON file storage")
        
        # Fallback to JSON file
        return self._save_to_json(chat_id, data)
    
    def load_chat_history(self, chat_id: str) -> List[Dict]:
        """
        Load chat history from MongoDB or JSON file as fallback.
        
        Args:
            chat_id: Chat session ID
            
        Returns:
            List of chat messages
        """
        # Try MongoDB first
        if self.mongo_available:
            try:
                data = self.collection.find_one({"chat_id": chat_id})
                if data:
                    app_logger.info(f"Loaded chat history from MongoDB for chat_id={chat_id}")
                    return data.get("messages", [])
            except Exception as e:
                error_logger.error(f"Failed to load from MongoDB for chat_id={chat_id}: {e}")
                app_logger.info("Falling back to JSON file storage")
        
        # Fallback to JSON file
        return self._load_from_json(chat_id)
    
    def get_chat_history(self, chat_id: str) -> Dict:
        """
        Get full chat history for a chat session.
        
        Args:
            chat_id: Chat session ID
            
        Returns:
            Chat data dictionary
        """
        # Try MongoDB first
        if self.mongo_available:
            try:
                data = self.collection.find_one({"chat_id": chat_id})
                if data:
                    # Remove MongoDB's _id field
                    data.pop("_id", None)
                    app_logger.info(f"Retrieved full chat history from MongoDB for chat_id={chat_id}")
                    return data
            except Exception as e:
                error_logger.error(f"Failed to get chat from MongoDB for chat_id={chat_id}: {e}")
                app_logger.info("Falling back to JSON file storage")
        
        # Fallback to JSON file
        chat_file = Path(settings.user_chat_folder) / f"{chat_id}.json"
        if chat_file.exists():
            try:
                with open(chat_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                error_logger.error(f"Failed to load chat history {chat_id} from JSON: {e}")
        
        return {"messages": []}
    
    def get_recent_chats(self, limit: int = 10) -> List[Dict]:
        """
        Get recent chat sessions.
        
        Args:
            limit: Maximum number of chats to return
            
        Returns:
            List of chat metadata (excludes empty chats)
        """
        # Try MongoDB first
        if self.mongo_available:
            try:
                chats = list(self.collection.find(
                    {},
                    {"_id": 0}  # Exclude MongoDB's _id field
                ).sort("updated_at", DESCENDING).limit(limit * 2))
                
                recent_chats = []
                for data in chats:
                    messages = data.get("messages", [])
                    
                    # Only include chats with at least 1 message
                    if len(messages) > 0:
                        # Get first user message as preview
                        preview = next(
                            (msg["content"][:50] + "..." if len(msg["content"]) > 50 else msg["content"]
                             for msg in messages if msg["role"] == "user"),
                            "No messages"
                        )
                        
                        recent_chats.append({
                            "chat_id": data.get("chat_id"),
                            "model_type": data.get("model_type", "unknown"),
                            "preview": preview,
                            "updated_at": data.get("updated_at"),
                            "message_count": len(messages)
                        })
                        
                        if len(recent_chats) >= limit:
                            break
                
                app_logger.info(f"Retrieved {len(recent_chats)} recent chats from MongoDB")
                return recent_chats
                
            except Exception as e:
                error_logger.error(f"Failed to get recent chats from MongoDB: {e}")
                app_logger.info("Falling back to JSON file storage")
        
        # Fallback to JSON files
        return self._get_recent_chats_from_json(limit)
    
    def _save_to_json(self, chat_id: str, data: Dict) -> bool:
        """Save chat history to JSON file."""
        chat_file = Path(settings.user_chat_folder) / f"{chat_id}.json"
        
        try:
            with open(chat_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            app_logger.info(f"Saved chat history to JSON file for chat_id={chat_id}")
            return True
            
        except Exception as e:
            error_logger.error(f"Failed to save chat history to JSON {chat_id}: {e}")
            return False
    
    def _load_from_json(self, chat_id: str) -> List[Dict]:
        """Load chat history from JSON file."""
        chat_file = Path(settings.user_chat_folder) / f"{chat_id}.json"
        
        if chat_file.exists():
            try:
                with open(chat_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get("messages", [])
            except Exception as e:
                error_logger.error(f"Failed to load chat history {chat_id} from JSON: {e}")
        
        return []
    
    def _get_recent_chats_from_json(self, limit: int) -> List[Dict]:
        """Get recent chats from JSON files."""
        chat_folder = Path(settings.user_chat_folder)
        chat_files = sorted(
            chat_folder.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        recent_chats = []
        for chat_file in chat_files[:limit * 2]:  # Get more to filter out empty ones
            try:
                with open(chat_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    messages = data.get("messages", [])
                    
                    # Only include chats with at least 1 message
                    if len(messages) > 0:
                        # Get first user message as preview
                        preview = next(
                            (msg["content"][:50] + "..." if len(msg["content"]) > 50 else msg["content"]
                             for msg in messages if msg["role"] == "user"),
                            "No messages"
                        )
                        
                        recent_chats.append({
                            "chat_id": data.get("chat_id"),
                            "model_type": data.get("model_type", "unknown"),
                            "preview": preview,
                            "updated_at": data.get("updated_at"),
                            "message_count": len(messages)
                        })
                        
                        if len(recent_chats) >= limit:
                            break
            except Exception as e:
                error_logger.error(f"Failed to load chat file {chat_file}: {e}")
        
        return recent_chats
    
    def close(self):
        """Close MongoDB connection."""
        if self.client:
            try:
                self.client.close()
                app_logger.info("Closed MongoDB connection")
            except Exception as e:
                error_logger.error(f"Error closing MongoDB connection: {e}")
