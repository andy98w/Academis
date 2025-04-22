#!/usr/bin/env python3
import os
import sys
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv

load_dotenv()

# MongoDB connection
MONGODB_URI = os.getenv("MONGODB_URI")
if not MONGODB_URI:
    raise ValueError("MONGODB_URI environment variable is not set")
client = MongoClient(MONGODB_URI, server_api=ServerApi("1"))
db = client.Academis
COLLECTION_NAME = "economics"

def check_collection():
    collection = db[COLLECTION_NAME]
    
    count = collection.count_documents({})
    print(f"Total number of documents in {COLLECTION_NAME} collection: {count}")
    
    if count > 0:
        sample_doc = collection.find_one()
        print("\nSample document structure:")
        for key, value in sample_doc.items():
            if key == 'embedding':
                print(f"{key}: [vector of length {len(value)}]")
            elif isinstance(value, str) and len(value) > 100:
                print(f"{key}: {value[:100]}... (truncated)")
            else:
                print(f"{key}: {value}")
        
        has_content = collection.count_documents({"page_content": {"$exists": True}})
        print(f"\nDocuments with 'page_content' field: {has_content}")
        
        print("\nSample document contents:")
        for doc in collection.find({"page_content": {"$exists": True}}).limit(3):
            content = doc.get("page_content", "No content")
            if isinstance(content, str):
                print(f"- {content[:150]}...")
            else:
                print(f"- Content is not a string: {type(content)}")
        
        has_embedding = collection.count_documents({"embedding": {"$exists": True}})
        print(f"\nDocuments with 'embedding' field: {has_embedding}")
        
        print("\nMetadata fields found:")
        metadata_fields = set()
        for doc in collection.find().limit(100):
            for key in doc.keys():
                if key not in ['_id', 'embedding', 'page_content']:
                    metadata_fields.add(key)
        
        for field in metadata_fields:
            field_count = collection.count_documents({field: {"$exists": True}})
            print(f"- {field}: {field_count} documents")
    
    else:
        print("Collection is empty.")

if __name__ == "__main__":
    check_collection()