#!/usr/bin/env python
"""
Test MongoDB Atlas connection.

Run this script to verify your MongoDB Atlas setup is working correctly.
Make sure to set MONGO_URI environment variable before running.

Example:
    export MONGO_URI="mongodb+srv://user:pass@cluster.mongodb.net/?retryWrites=true"
    python test_mongodb_connection.py
"""
import os
import sys
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app.core.chat_storage import ChatStorageService
    from app.utils.logging_config import app_logger
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running this from the project root directory.")
    sys.exit(1)


def test_mongodb_connection():
    """Test MongoDB connection and basic operations."""
    print("=" * 70)
    print("MongoDB Atlas Connection Test")
    print("=" * 70)
    print()
    
    # Check if MONGO_URI is set
    import os as os_module
    mongo_uri = os_module.getenv("MONGO_URI", "")
    if not mongo_uri:
        print("⚠️  MONGO_URI environment variable not set")
        print("   The application will use JSON file fallback mode.")
        print()
        print("To test MongoDB Atlas connection, set MONGO_URI:")
        print('   export MONGO_URI="mongodb+srv://user:pass@cluster.mongodb.net/?retryWrites=true"')
        print()
    else:
        print(f"✓ MONGO_URI is set: {mongo_uri[:30]}...")
        print()
    
    # Initialize chat storage
    print("Initializing ChatStorageService...")
    try:
        storage = ChatStorageService()
        print()
        
        if storage.mongo_available:
            print("✓ MongoDB Atlas connection successful!")
            print(f"  Database: {storage.db.name}")
            print(f"  Collection: {storage.collection.name}")
            print()
            
            # Test write operation
            print("Testing write operation...")
            test_chat_id = f"test-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            test_messages = [
                {
                    "role": "user",
                    "content": "Test message",
                    "timestamp": datetime.now().isoformat()
                },
                {
                    "role": "assistant",
                    "content": "Test response",
                    "timestamp": datetime.now().isoformat(),
                    "thinking": None,
                    "sources": []
                }
            ]
            
            result = storage.save_chat_history(test_chat_id, test_messages, "gemini")
            if result:
                print("✓ Write operation successful")
                print()
                
                # Test read operation
                print("Testing read operation...")
                loaded = storage.load_chat_history(test_chat_id)
                if len(loaded) == 2:
                    print("✓ Read operation successful")
                    print(f"  Loaded {len(loaded)} messages")
                    print()
                    
                    # Test get recent chats
                    print("Testing get recent chats...")
                    recent = storage.get_recent_chats(limit=1)
                    if recent:
                        print("✓ Get recent chats successful")
                        print(f"  Found {len(recent)} recent chat(s)")
                        print()
                    else:
                        print("⚠️  No recent chats found")
                        print()
                    
                    # Cleanup test data
                    print("Cleaning up test data...")
                    try:
                        storage.collection.delete_one({"chat_id": test_chat_id})
                        print("✓ Test data cleaned up")
                    except Exception as e:
                        print(f"⚠️  Failed to cleanup: {e}")
                    
                    print()
                    print("=" * 70)
                    print("✓ All MongoDB tests passed!")
                    print("=" * 70)
                    return True
                else:
                    print(f"❌ Read operation failed: Expected 2 messages, got {len(loaded)}")
            else:
                print("❌ Write operation failed")
        else:
            print("⚠️  MongoDB not available - using JSON file fallback")
            print()
            print("Reasons this might happen:")
            print("  1. MONGO_URI not set or invalid")
            print("  2. Network connectivity issues")
            print("  3. MongoDB Atlas IP whitelist doesn't include your IP")
            print("  4. Invalid credentials in MONGO_URI")
            print()
            
            # Test JSON fallback
            print("Testing JSON fallback mode...")
            test_chat_id = f"test-fallback-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            test_messages = [
                {
                    "role": "user",
                    "content": "Fallback test",
                    "timestamp": datetime.now().isoformat()
                }
            ]
            
            result = storage.save_chat_history(test_chat_id, test_messages, "gemini")
            if result:
                loaded = storage.load_chat_history(test_chat_id)
                if loaded:
                    print("✓ JSON fallback mode working correctly")
                    print()
                    
                    # Cleanup
                    import os
                    from pathlib import Path
                    from app.config import settings
                    json_file = Path(settings.user_chat_folder) / f"{test_chat_id}.json"
                    if json_file.exists():
                        os.remove(json_file)
                        print("✓ Test data cleaned up")
                    
                    print()
                    print("=" * 70)
                    print("✓ JSON fallback mode is working!")
                    print("=" * 70)
                    return True
            
            print("❌ JSON fallback test failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_mongodb_connection()
    sys.exit(0 if success else 1)
