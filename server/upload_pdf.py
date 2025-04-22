import os
import asyncio
import argparse
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_mongodb import MongoDBAtlasVectorSearch
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
if not MONGODB_URI:
    raise ValueError("MONGODB_URI environment variable is not set")
client = MongoClient(MONGODB_URI, server_api=ServerApi("1"))
db = client.Academis
COLLECTION_NAME = "economics"

async def upload_pdf(pdf_path):
    if not os.path.exists(pdf_path):
        print(f"PDF file not found: {pdf_path}")
        return

    try:
        embeddings = OpenAIEmbeddings()
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
        )

        loader = PyPDFLoader(pdf_path)
        pages = loader.load()

        if not pages:
            print(f"No content found in PDF: {pdf_path}")
            return

        print(f"Loaded {len(pages)} pages from PDF")
        splits = text_splitter.split_documents(pages)
        print(f"Created {len(splits)} chunks from the PDF")

        collection = db[COLLECTION_NAME]
        existing_count = collection.count_documents({})

        if existing_count == 0:
            vector_store = MongoDBAtlasVectorSearch.from_documents(
                documents=splits,
                embedding=embeddings,
                collection=collection,
                index_name="economics_vector_index",
            )
        else:
            vector_store = MongoDBAtlasVectorSearch(
                collection_name=COLLECTION_NAME,
                embedding=embeddings,
                collection=collection,
                index_name="economics_vector_index",
            )
            vector_store.add_documents(splits)

        print(f"Successfully uploaded PDF to MongoDB Atlas ({len(splits)} chunks)")
    except Exception as e:
        print(f"Error uploading PDF: {e}")

async def main():
    parser = argparse.ArgumentParser(
        description="Upload a PDF to MongoDB Atlas Vector Search"
    )
    parser.add_argument("--pdf", help="Path to the PDF file")

    args = parser.parse_args()
    pdf_path = args.pdf

    if not pdf_path:
        for root, _, files in os.walk(os.path.join(os.path.dirname(__file__), "data")):
            for file in files:
                if file.endswith(".pdf"):
                    pdf_path = os.path.join(root, file)
                    print(f"Found PDF file: {pdf_path}")
                    break
            if pdf_path:
                break

    if not pdf_path:
        print("Error: No PDF file specified or found in data directory")
        return

    await upload_pdf(pdf_path)

if __name__ == "__main__":
    asyncio.run(main())