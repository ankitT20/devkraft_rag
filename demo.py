#!/usr/bin/env python3
"""
Demo script showing how to use the DevKraft RAG API programmatically.
"""
import requests
import time
import json
from pathlib import Path

# API Configuration
API_URL = "http://localhost:8000"


def check_health():
    """Check if the API is running."""
    print("🔍 Checking API health...")
    try:
        response = requests.get(f"{API_URL}/health")
        if response.status_code == 200:
            print("✅ API is healthy!")
            return True
        else:
            print(f"❌ API returned status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API. Make sure it's running at http://localhost:8000")
        return False


def upload_document(file_path: str):
    """Upload a document to the RAG system."""
    print(f"\n📤 Uploading document: {file_path}")
    
    if not Path(file_path).exists():
        print(f"❌ File not found: {file_path}")
        return False
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (Path(file_path).name, f, 'application/octet-stream')}
            response = requests.post(f"{API_URL}/upload", files=files)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Upload successful!")
            print(f"   Message: {result['message']}")
            return True
        else:
            print(f"❌ Upload failed with status code: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return False


def query_rag(query: str, model_type: str = "gemini", chat_id: str = None):
    """Send a query to the RAG system."""
    print(f"\n💬 Query: {query}")
    print(f"🤖 Model: {model_type}")
    
    try:
        payload = {
            "query": query,
            "model_type": model_type
        }
        if chat_id:
            payload["chat_id"] = chat_id
        
        response = requests.post(f"{API_URL}/query", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n🤖 Response:")
            print(f"   {result['response']}")
            
            if result.get('thinking'):
                print(f"\n🧠 Thinking:")
                print(f"   {result['thinking']}")
            
            print(f"\n💾 Chat ID: {result['chat_id']}")
            return result['chat_id']
        else:
            print(f"❌ Query failed with status code: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Query error: {e}")
        return None


def get_recent_chats():
    """Get recent chat sessions."""
    print("\n📋 Fetching recent chats...")
    
    try:
        response = requests.get(f"{API_URL}/chats?limit=5")
        
        if response.status_code == 200:
            chats = response.json()
            print(f"✅ Found {len(chats)} recent chats:")
            for i, chat in enumerate(chats, 1):
                print(f"\n   {i}. Chat ID: {chat['chat_id']}")
                print(f"      Model: {chat['model_type']}")
                print(f"      Preview: {chat['preview']}")
                print(f"      Messages: {chat['message_count']}")
                print(f"      Updated: {chat['updated_at']}")
            return chats
        else:
            print(f"❌ Failed to fetch chats: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Error fetching chats: {e}")
        return []


def main():
    """Run the demo."""
    print("=" * 60)
    print("🤖 DevKraft RAG - API Demo")
    print("=" * 60)
    
    # Step 1: Check if API is running
    if not check_health():
        print("\n⚠️  Please start the API server first:")
        print("   ./start_api.sh")
        print("   or")
        print("   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000")
        return
    
    # Step 2: Upload a document (if you have one)
    print("\n" + "=" * 60)
    print("Step 1: Document Upload")
    print("=" * 60)
    
    # Check if test document exists
    test_doc = "generate_embeddings/stored_in_q_cloud_only/test_doc.txt"
    if Path(test_doc).exists():
        print(f"ℹ️  Test document already processed: {test_doc}")
    else:
        print("ℹ️  No documents to upload in this demo.")
        print("   You can upload documents via the Streamlit UI or API.")
    
    # Step 3: Query the RAG system
    print("\n" + "=" * 60)
    print("Step 2: RAG Queries")
    print("=" * 60)
    
    # Query 1: Using Gemini
    chat_id = query_rag(
        query="What are the key features of DevKraft RAG?",
        model_type="gemini"
    )
    
    time.sleep(2)
    
    # Query 2: Follow-up in same chat
    if chat_id:
        print("\n" + "-" * 60)
        query_rag(
            query="How do I get started?",
            model_type="gemini",
            chat_id=chat_id
        )
    
    time.sleep(2)
    
    # Query 3: Using Qwen3 (if available)
    print("\n" + "-" * 60)
    query_rag(
        query="What document formats are supported?",
        model_type="qwen3"
    )
    
    # Step 4: View chat history
    print("\n" + "=" * 60)
    print("Step 3: Chat History")
    print("=" * 60)
    
    get_recent_chats()
    
    # Done
    print("\n" + "=" * 60)
    print("✅ Demo completed!")
    print("=" * 60)
    print("\n💡 Try the Streamlit UI for a better experience:")
    print("   http://localhost:8501")
    print("\n📚 API Documentation:")
    print("   http://localhost:8000/docs")


if __name__ == "__main__":
    main()
