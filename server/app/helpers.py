"""
Helper functions for textbook content management and database operations
"""

import os
import json
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

def load_toc_from_file(subject: str) -> Optional[dict]:
    """Load table of contents from JSON file in toc directory"""
    try:
        toc_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "toc")
        toc_file = os.path.join(toc_dir, f"{subject}_toc.json")
        
        if os.path.exists(toc_file):
            with open(toc_file, 'r') as f:
                toc_data = json.load(f)
                # Convert string keys to integers for units
                if "units" in toc_data:
                    toc_data["units"] = {int(k): v for k, v in toc_data["units"].items()}
                return toc_data
        else:
            logger.warning(f"TOC file not found: {toc_file}")
            return None
    except Exception as e:
        logger.error(f"Error loading TOC from file: {e}")
        return None

def load_chapter_topics(subject: str) -> Dict[str, List[str]]:
    """Load chapter topics from TOC file"""
    try:
        toc_data = load_toc_from_file(subject)
        if not toc_data:
            return {}
            
        topics_dict = {}
        for unit_data in toc_data.get("units", {}).values():
            for chapter in unit_data.get("chapters", []):
                chapter_number = chapter.get("chapter_number")
                topics = chapter.get("topics", [])
                if chapter_number and topics:
                    topics_dict[chapter_number] = topics
        
        return topics_dict
        
    except Exception as e:
        logger.error(f"Error loading chapter topics from TOC: {e}")
        return {}

def get_chapter_data(textbook_collection, subject: str, unit: int, chapter_key: str, chapter_title: str) -> tuple:
    """Get chapter content, graph data, and quiz in a single MongoDB query.
    Returns (content_list, graph_data, quiz_data) tuple."""
    try:
        mongo_doc = textbook_collection.find_one({"chapter_id": chapter_key, "subject": subject})

        # Extract content
        content = ["Content not available yet."]
        if mongo_doc and "content" in mongo_doc and mongo_doc["content"]:
            logger.info(f"Found AI-generated content for {chapter_key} in MongoDB")
            raw_content = mongo_doc["content"]

            preview_text = "Content not available yet."
            for i, para in enumerate(raw_content):
                para_lower = para.strip().lower()
                if para_lower.startswith('## conclusion') or para_lower.startswith('## summary'):
                    # Check if heading element itself contains body text after \n
                    body = None
                    if '\n' in para:
                        body = para.split('\n', 1)[1].strip()
                    elif i + 1 < len(raw_content) and raw_content[i + 1].strip():
                        body = raw_content[i + 1].strip()

                    if body:
                        if body.startswith('**Key Takeaways:**'):
                            body = body.replace('**Key Takeaways:**', '').strip()
                        sentences = body.split('. ')
                        if sentences:
                            preview_text = sentences[0]
                            if not preview_text.endswith('.'):
                                preview_text += '.'
                    break

            content = [preview_text] + raw_content
        else:
            logger.info(f"No content available for {chapter_key}")

        # Extract graph data
        graph_data = None
        if mongo_doc:
            if "graphs" in mongo_doc and mongo_doc["graphs"]:
                graph_data = mongo_doc["graphs"]
            elif "graph" in mongo_doc and mongo_doc["graph"]:
                graph_data = {"main": mongo_doc["graph"]}

        # Extract quiz data
        quiz_data = None
        if mongo_doc and "quiz" in mongo_doc and mongo_doc["quiz"]:
            quiz_data = mongo_doc["quiz"]

        return content, graph_data, quiz_data
    except Exception as e:
        logger.error(f"Error accessing MongoDB for {chapter_key}: {e}")
        return [f"Error loading content: {str(e)}"], None, None

def get_chapter_specific_topics(chapter: str, chapter_title: str, subject: str) -> str:
    """Get the specific topics that should be covered in this chapter"""
    try:
        topics_data = load_chapter_topics(subject)
        if chapter in topics_data:
            topics_list = topics_data[chapter]
            # Convert list to formatted string
            return "\n".join([f"- {topic}" for topic in topics_list])
        
        # Fallback if chapter not found
        logger.warning(f"Chapter topics not found for {chapter}, using default")
        return f"- {chapter_title}: Core concepts and applications"
        
    except Exception as e:
        logger.error(f"Error loading chapter topics: {e}")
        return f"- {chapter_title}: Core concepts and applications"

def get_main_section_title(chapter_title: str) -> str:
    """Get the main section title based on chapter title"""
    # Extract first main concept from title (works for any subject)
    if " and " in chapter_title:
        return chapter_title.split(" and ")[0]
    elif ": " in chapter_title:
        return chapter_title.split(": ")[0]
    else:
        # Just return the full title if no natural split point
        return chapter_title

def validate_and_clean_content(paragraphs: List[str], subject: str, unit: int, chapter: str, toc: dict) -> List[str]:
    """Validate and clean content to ensure MongoDB compatibility"""
    import re as _re
    cleaned_paragraphs = []
    prev_was_heading = False

    for para in paragraphs:
        if para and isinstance(para, str):
            # Ensure the paragraph is a clean string
            cleaned_para = str(para).strip()
            if cleaned_para:
                # Check if this is a heading
                is_heading = cleaned_para.startswith('## ')

                # Skip bold-only lines that duplicate a heading (e.g., **Introduction** after ## Introduction)
                if prev_was_heading and cleaned_para.startswith('**') and cleaned_para.endswith('**'):
                    prev_was_heading = False
                    continue

                # Skip redundant chapter title headings (e.g., "## Chapter 1.1: ...")
                if is_heading and _re.match(r'^## Chapter \d+\.\d+', cleaned_para):
                    continue

                cleaned_paragraphs.append(cleaned_para)
                prev_was_heading = is_heading
    
    if not cleaned_paragraphs:
        chapter_title = f"Chapter {chapter}"
        unit_title = toc.get("units", {}).get(unit, {}).get("title", f"Unit {unit}")
        
        logger.warning(f"No valid content generated for {subject} Unit {unit}, Chapter {chapter}")
        cleaned_paragraphs = [
            f"This chapter covers {chapter_title} within {unit_title}.",
            f"It explores key concepts and applications related to {chapter_title}.",
            f"Students will learn about the theoretical frameworks and practical implications of {chapter_title} in {subject}."
        ]
    
    return cleaned_paragraphs