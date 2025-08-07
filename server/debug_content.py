#!/usr/bin/env python3
"""
Debug script for textbook content issues
"""
import os
import sys
from pymongo import MongoClient
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_environment():
    """Check environment setup"""
    print("=== ENVIRONMENT CHECK ===")
    
    # Check if .env exists
    if os.path.exists('.env'):
        print("✓ .env file found")
    else:
        print("✗ .env file NOT found")
        return False
    
    # Load environment variables
    load_dotenv()
    
    # Check MongoDB URI
    mongodb_uri = os.getenv('MONGODB_URI')
    if mongodb_uri:
        print("✓ MONGODB_URI is set")
        # Don't print the actual URI for security
        print(f"  Connecting to: {mongodb_uri.split('@')[1].split('/')[0]}")
    else:
        print("✗ MONGODB_URI is NOT set")
        return False
    
    # Check OpenAI API key
    openai_key = os.getenv('OPENAI_API_KEY')
    if openai_key:
        print("✓ OPENAI_API_KEY is set")
    else:
        print("✗ OPENAI_API_KEY is NOT set")
        return False
    
    return True

def check_mongodb_connection():
    """Test MongoDB connection"""
    print("\n=== MONGODB CONNECTION CHECK ===")
    
    try:
        client = MongoClient(os.getenv('MONGODB_URI'))
        # Test connection
        client.server_info()
        print("✓ Successfully connected to MongoDB")
        
        # Check database
        db = client['academis']
        print(f"✓ Using database: academis")
        
        # Check collections
        collections = db.list_collection_names()
        print(f"✓ Found {len(collections)} collections:")
        for col in collections:
            print(f"  - {col}")
        
        return client, db
        
    except Exception as e:
        print(f"✗ MongoDB connection failed: {e}")
        return None, None

def check_textbook_content(db):
    """Check textbook content in database"""
    print("\n=== TEXTBOOK CONTENT CHECK ===")
    
    if not db:
        print("✗ No database connection")
        return
    
    try:
        textbook_collection = db.textbook_content
        
        # Count documents
        total_docs = textbook_collection.count_documents({})
        print(f"Total textbook documents: {total_docs}")
        
        if total_docs == 0:
            print("✗ No textbook content found!")
            print("\nTo generate content:")
            print("1. Make sure the server is running: python -m uvicorn app.main:app --reload")
            print("2. Generate content for a chapter:")
            print("   curl -X POST http://localhost:8080/api/textbook/generate/micro \\")
            print("   -H 'Content-Type: application/json' \\")
            print("   -d '{\"unit\": 1, \"chapter\": \"1.1\"}'")
            return
        
        # Check specific chapters
        print("\nChecking specific chapters:")
        for chapter_id in ['1.1', '1.2', '2.1']:
            doc = textbook_collection.find_one({'chapter_id': chapter_id})
            if doc:
                content_length = len(doc.get('content', []))
                has_graph = 'graph' in doc or 'graphs' in doc
                print(f"✓ Chapter {chapter_id}: {content_length} paragraphs, graph: {has_graph}")
            else:
                print(f"✗ Chapter {chapter_id}: NOT FOUND")
        
        # Show sample content
        sample = textbook_collection.find_one()
        if sample:
            print(f"\nSample document structure:")
            print(f"  - chapter_id: {sample.get('chapter_id')}")
            print(f"  - subject: {sample.get('subject')}")
            print(f"  - unit: {sample.get('unit')}")
            print(f"  - chapter: {sample.get('chapter')}")
            print(f"  - content length: {len(sample.get('content', []))}")
            print(f"  - has graph: {'graph' in sample or 'graphs' in sample}")
            
    except Exception as e:
        print(f"✗ Error checking textbook content: {e}")

def check_api_endpoints():
    """Test API endpoints"""
    print("\n=== API ENDPOINT CHECK ===")
    
    import requests
    
    base_url = "http://localhost:8080"
    
    # Check if server is running
    try:
        response = requests.get(f"{base_url}/api/health", timeout=2)
        if response.status_code == 200:
            print("✓ Server is running")
        else:
            print(f"✗ Server returned status: {response.status_code}")
            return
    except Exception as e:
        print(f"✗ Server is NOT running: {e}")
        print("\nStart the server with:")
        print("  cd /path/to/server")
        print("  python -m uvicorn app.main:app --reload")
        return
    
    # Test textbook endpoints
    endpoints = [
        "/api/textbook/micro/toc",
        "/api/textbook/micro/unit/1",
        "/api/textbook/micro/unit/1/chapter/1.1"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}")
            if response.status_code == 200:
                data = response.json()
                if 'error' in data:
                    print(f"✗ {endpoint}: Error - {data['error']}")
                else:
                    print(f"✓ {endpoint}: OK")
            else:
                print(f"✗ {endpoint}: Status {response.status_code}")
        except Exception as e:
            print(f"✗ {endpoint}: {e}")

def main():
    """Run all checks"""
    print("TEXTBOOK CONTENT DEBUGGER")
    print("=" * 50)
    
    # Check environment
    if not check_environment():
        print("\n❌ Fix environment issues first!")
        return
    
    # Check MongoDB
    client, db = check_mongodb_connection()
    
    # Check content
    check_textbook_content(db)
    
    # Check API
    check_api_endpoints()
    
    print("\n" + "=" * 50)
    print("DEBUGGING COMPLETE")
    
    if client:
        client.close()

if __name__ == "__main__":
    main()