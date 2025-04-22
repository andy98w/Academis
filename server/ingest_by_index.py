#!/usr/bin/env python3
import os
import asyncio
import sys
from upload_pdf import upload_pdf

async def ingest_pdf_by_index(index):
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    
    if not os.path.exists(data_dir):
        print(f"Data directory not found: {data_dir}")
        return
    
    pdf_files = [f for f in os.listdir(data_dir) if f.lower().endswith('.pdf')]
    pdf_files.sort()
    
    if not pdf_files:
        print("No PDF files found in data directory")
        return
    
    if index < 0 or index >= len(pdf_files):
        print(f"Invalid index: {index}. Must be between 0 and {len(pdf_files)-1}")
        return
    
    pdf_filename = pdf_files[index]
    pdf_path = os.path.join(data_dir, pdf_filename)
    
    print(f"Processing file {index+1} of {len(pdf_files)}: {pdf_filename}")
    await upload_pdf(pdf_path)
    print(f"Completed: {pdf_filename}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ingest_by_index.py <index>")
        print("Example: python ingest_by_index.py 0")
        sys.exit(1)
    
    try:
        index = int(sys.argv[1])
        asyncio.run(ingest_pdf_by_index(index))
    except ValueError:
        print("Error: Index must be an integer")
        sys.exit(1)