"""
Helper functions for textbook content management and database operations
"""

import os
import json
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

def load_toc_from_file(subject: str) -> Optional[dict]:
    """Load table of contents from JSON file in data directory"""
    try:
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        toc_file = os.path.join(data_dir, f"{subject}_toc.json")
        
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

def load_chapter_topics(subject: str = "micro") -> Dict[str, List[str]]:
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

def get_chapter_content_with_preview(textbook_collection, subject: str, unit: int, chapter_key: str, chapter_title: str) -> List[str]:
    """Helper function to get chapter content with conclusion preview"""
    mongo_key = chapter_key
    try:
        mongo_doc = textbook_collection.find_one({"chapter_id": mongo_key})
        
        if mongo_doc and "content" in mongo_doc and mongo_doc["content"]:
            logger.info(f"Found AI-generated content for {mongo_key} in MongoDB")
            content = mongo_doc["content"]
            
            preview_text = "Content not available yet."
            for i, para in enumerate(content):
                if para.strip().lower().startswith('## conclusion') or para.strip().lower().startswith('## summary'):
                    if i + 1 < len(content) and content[i + 1].strip():
                        conclusion_para = content[i + 1].strip()
                        # Look for **Key Takeaways:** format
                        if conclusion_para.startswith('**Key Takeaways:**'):
                            # Extract first sentence after Key Takeaways
                            text_after_takeaways = conclusion_para.replace('**Key Takeaways:**', '').strip()
                            sentences = text_after_takeaways.split('. ')
                            if sentences:
                                preview_text = sentences[0]
                                if not preview_text.endswith('.'):
                                    preview_text += '.'
                        else:
                            sentences = conclusion_para.split('. ')
                            if sentences:
                                preview_text = sentences[0]
                                if not preview_text.endswith('.'):
                                    preview_text += '.'
                        break
            
            return [preview_text] + content
        else:
            logger.info(f"No content available for {chapter_key}")
            return ["Content not available yet."]
    except Exception as e:
        logger.error(f"Error accessing MongoDB for {mongo_key}: {e}")
        return [f"Error loading content: {str(e)}"]

def get_chapter_graph_data(textbook_collection, subject: str, unit: int, chapter_key: str):
    """Get graph data for a chapter if available"""
    mongo_key = chapter_key
    try:
        mongo_doc = textbook_collection.find_one({"chapter_id": mongo_key})
        if mongo_doc:
            # Check for new multiple graphs format first
            if "graphs" in mongo_doc and mongo_doc["graphs"]:
                return mongo_doc["graphs"]
            # Fall back to old single graph format
            elif "graph" in mongo_doc and mongo_doc["graph"]:
                return {"main": mongo_doc["graph"]}
        return None
    except Exception as e:
        logger.error(f"Error getting graph data for {mongo_key}: {e}")
        return None

def get_chapter_specific_topics(chapter: str, chapter_title: str, subject: str = "micro") -> str:
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
    if "Scarcity and Choice" in chapter_title:
        return "Scarcity"
    elif "Opportunity Cost" in chapter_title:
        return "Opportunity Cost and PPF"
    elif "Comparative Advantage" in chapter_title:
        return "Comparative Advantage"
    elif "Economic Systems" in chapter_title:
        return "Economic Systems"
    else:
        # Extract first main concept
        return chapter_title.split(" and ")[0]

def validate_and_clean_content(paragraphs: List[str], subject: str, unit: int, chapter: str, toc: dict) -> List[str]:
    """Validate and clean content to ensure MongoDB compatibility"""
    cleaned_paragraphs = []
    for para in paragraphs:
        if para and isinstance(para, str):
            # Ensure the paragraph is a clean string
            cleaned_para = str(para).strip()
            if cleaned_para:
                cleaned_paragraphs.append(cleaned_para)
    
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