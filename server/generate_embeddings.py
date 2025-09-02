#!/usr/bin/env python3
"""
Generate embeddings for existing documents in MongoDB that don't have embeddings.
This script will add embedding vectors to all documents in the economics collection.
"""

import os
import asyncio
from typing import List, Dict, Any
from dotenv import load_dotenv
from pymongo import MongoClient
from langchain_openai import OpenAIEmbeddings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv(override=True)

async def generate_embeddings_for_collection():
    """Generate embeddings for all documents that don't have them"""
    
    # Connect to MongoDB
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        logger.error("MONGODB_URI not found in environment variables")
        return
    
    client = MongoClient(mongodb_uri)
    db = client.Academis
    collection = db.economics
    
    # Initialize OpenAI embeddings
    embeddings = OpenAIEmbeddings()
    
    # Find documents without embeddings
    documents_without_embeddings = list(collection.find({"embedding": {"$exists": False}}))
    total_docs = len(documents_without_embeddings)
    
    logger.info(f"Found {total_docs} documents without embeddings")
    
    if total_docs == 0:
        logger.info("All documents already have embeddings")
        return
    
    batch_size = 100  # Process in batches to avoid overwhelming the API
    processed = 0
    
    for i in range(0, total_docs, batch_size):
        batch = documents_without_embeddings[i:i + batch_size]
        
        logger.info(f"Processing batch {i//batch_size + 1}/{(total_docs + batch_size - 1)//batch_size}")
        
        # Extract texts for this batch
        texts = []
        doc_ids = []
        
        for doc in batch:
            if 'text' in doc and doc['text']:
                texts.append(doc['text'])
                doc_ids.append(doc['_id'])
            else:
                logger.warning(f"Document {doc['_id']} has no text field")
        
        if not texts:
            continue
        
        try:
            # Generate embeddings for the batch
            logger.info(f"Generating embeddings for {len(texts)} documents...")
            embedding_vectors = await embeddings.aembed_documents(texts)
            
            # Update documents with embeddings
            for doc_id, embedding_vector in zip(doc_ids, embedding_vectors):
                collection.update_one(
                    {"_id": doc_id},
                    {"$set": {"embedding": embedding_vector}}
                )
                processed += 1
            
            logger.info(f"Updated {len(embedding_vectors)} documents with embeddings (Total: {processed}/{total_docs})")
            
        except Exception as e:
            logger.error(f"Error processing batch: {e}")
            continue
    
    logger.info(f"Completed! Generated embeddings for {processed} documents")
    
    # Verify the results
    docs_with_embeddings = collection.count_documents({"embedding": {"$exists": True}})
    logger.info(f"Total documents with embeddings: {docs_with_embeddings}")

if __name__ == "__main__":
    asyncio.run(generate_embeddings_for_collection())