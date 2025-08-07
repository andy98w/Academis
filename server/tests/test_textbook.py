#!/usr/bin/env python3
"""
Comprehensive test utilities for textbook generation and content management
"""

import sys
import os
import asyncio
sys.path.insert(0, '/Users/andywu/Academis/server')

from app.rag_service import db
from app.textbook_service import generate_textbook_content

async def delete_chapter_content(subject: str, unit: int, chapter: str):
    """Delete existing chapter content from MongoDB"""
    if db is None:
        print("MongoDB not available")
        return
        
    textbook_collection = db.textbook_content
    chapter_key = chapter
    result = textbook_collection.delete_many({"chapter_id": chapter_key})
    print(f"Deleted {result.deleted_count} documents for {chapter_key}")

async def test_generation(subject: str, unit: int, chapter: str):
    """Test textbook generation for a specific chapter"""
    try:
        print(f"Testing textbook generation for {subject} Unit {unit}, Chapter {chapter}...")
        result = await generate_textbook_content(subject, unit, chapter)
        
        print(f"\nGenerated {len(result)} paragraphs:")
        for i, paragraph in enumerate(result[:3]):  # Show first 3 paragraphs
            print(f"\nParagraph {i+1}:")
            print(paragraph[:200] + "..." if len(paragraph) > 200 else paragraph)
            
        if len(result) > 3:
            print(f"\n... and {len(result) - 3} more paragraphs")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def view_chapter_content(subject: str, unit: int, chapter: str, show_sections=True):
    """View existing chapter content"""
    if db is None:
        print("MongoDB not available")
        return
        
    textbook_collection = db.textbook_content
    chapter_key = chapter
    
    doc = textbook_collection.find_one({"chapter_id": chapter_key})
    if doc and "content" in doc:
        content = doc["content"]
        print(f"Found {len(content)} paragraphs for {chapter_key}\n")
        
        if show_sections:
            # Show section headers and key content
            for i, paragraph in enumerate(content):
                if paragraph.strip().startswith("##") or "**Key Takeaways**" in paragraph or "Question" in paragraph:
                    print(f"--- Paragraph {i+1} ---")
                    print(paragraph[:300] + "..." if len(paragraph) > 300 else paragraph)
                    print()
        else:
            # Show first few paragraphs
            for i, paragraph in enumerate(content[:5]):
                print(f"--- Paragraph {i+1} ---")
                print(paragraph)
                print()
            if len(content) > 5:
                print(f"... and {len(content) - 5} more paragraphs")
    else:
        print(f"No content found for {chapter_key}")

def check_formatting(subject: str, unit: int, chapter: str):
    """Check the formatting of questions and summary sections"""
    if db is None:
        print("MongoDB not available")
        return
        
    textbook_collection = db.textbook_content
    chapter_key = chapter
    
    doc = textbook_collection.find_one({"chapter_id": chapter_key})
    if doc and "content" in doc:
        content = doc["content"]
        
        print(f"=== FORMATTING CHECK FOR {chapter_key.upper()} ===\n")
        
        # Find questions and summary sections
        for i, paragraph in enumerate(content):
            if ("Question" in paragraph and any(char.isdigit() for char in paragraph[:20])) or \
               "**Solution:**" in paragraph or \
               "**Key Takeaways:**" in paragraph or \
               paragraph.strip() == "## Summary":
                print(f"--- Paragraph {i+1} ---")
                print(repr(paragraph))  # Show with escape characters for debugging
                print(paragraph)
                print()
    else:
        print(f"No content found for {chapter_key}")

async def regenerate_chapter(subject: str, unit: int, chapter: str):
    """Delete and regenerate chapter content"""
    print(f"Regenerating {subject} Unit {unit}, Chapter {chapter}...")
    await delete_chapter_content(subject, unit, chapter)
    await test_generation(subject, unit, chapter)

def check_sections(subject: str, unit: int, chapter: str):
    """Check what sections were generated in the content"""
    if db is None:
        print("MongoDB not available")
        return
        
    textbook_collection = db.textbook_content
    chapter_key = chapter
    
    doc = textbook_collection.find_one({"chapter_id": chapter_key})
    if doc and "content" in doc:
        content = doc["content"]
        print(f"Found {len(content)} paragraphs for {chapter_key}\n")
        
        # Find all section headers
        sections_found = []
        for i, paragraph in enumerate(content):
            if paragraph.strip().startswith("##"):
                sections_found.append(f"Paragraph {i+1}: {paragraph.strip()[:50]}")
        
        print("Sections found:")
        for section in sections_found:
            print(f"  {section}")
            
        # Check for any graph-related content when no graph was generated
        graph_content = []
        for i, paragraph in enumerate(content):
            if any(word in paragraph.lower() for word in ["visual", "graph", "curve", "axes", "plot"]):
                graph_content.append(f"Paragraph {i+1}: {paragraph[:100]}...")
        
        if graph_content:
            print(f"\nGraph-related content found:")
            for content_line in graph_content:
                print(f"  {content_line}")
    else:
        print(f"No content found for {chapter_key}")

if __name__ == "__main__":
    # Example usage - regenerate micro Unit 1.1
    asyncio.run(regenerate_chapter("micro", 1, "1.1"))