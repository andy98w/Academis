
import logging
from typing import Dict, List, Union, Optional
import datetime
import json
import os
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _get_chapter_content_with_preview(textbook_collection, subject: str, unit: int, chapter_key: str, chapter_title: str) -> List[str]:
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

def _get_chapter_graph_data(textbook_collection, subject: str, unit: int, chapter_key: str):
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

# TOC definitions moved to /data directory as JSON files

def _load_toc_from_file(subject: str) -> dict:
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

async def get_textbook_toc(subject: str) -> dict:
    """
    Get the table of contents for the specified subject.
    
    Args:
        subject: Subject identifier (e.g., "micro", "macro", "biology")
        
    Returns:
        Dictionary with textbook table of contents
    """
    logger.info(f"Getting {subject} textbook table of contents")
    
    try:
        # First try to load from data directory
        toc = _load_toc_from_file(subject)
        
        if toc:
            return toc
        
        # Fallback to subject config for backwards compatibility
        from .subject_config import SubjectConfig
        subject_config = SubjectConfig.get_subject_config(subject)
        toc = subject_config["toc"]
        
        if toc is None:
            logger.warning(f"TOC not yet implemented for {subject}")
            return {
                "type": subject,
                "units": {},
                "message": f"Content for {SubjectConfig.get_full_subject_name(subject)} is coming soon!"
            }
        
        return toc
    
    except Exception as e:
        logger.error(f"Error getting textbook TOC: {str(e)}")
        return {"error": str(e)}

async def get_textbook_content(subject: str, unit: int = None, chapter: str = None) -> dict:
    """
    Retrieve textbook content organized by units and chapters.
    Args:
        subject: Subject identifier (e.g., "micro", "macro", "biology")
        unit: Optional unit number
        chapter: Optional chapter name/title
    Returns:
        Dictionary with textbook content organized by units and chapters
    """
    logger.info(f"Retrieving {subject} textbook content for unit: {unit}, chapter: {chapter}")
    
    try:
        from .rag_service import db
        if db is None:
            raise ValueError("MongoDB connection not available")
        
        textbook_collection = db.textbook_content
        toc = await get_textbook_toc(subject)

        result = {
            "type": subject,
            "units": {}
        }
        
        if unit is not None:
            if unit not in toc["units"]:
                from .subject_config import SubjectConfig
                subject_name = SubjectConfig.get_subject_name(subject)
                raise ValueError(f"Unit {unit} not found in {subject_name} textbook")
                
            unit_data = toc["units"][unit]
            result["units"][unit] = {
                "title": unit_data["title"],
                "chapters": {}
            }
            
            if chapter:
                chapter_found = False
                for ch_data in unit_data["chapters"]:
                    if chapter.lower() in ch_data["title"].lower() or chapter == ch_data["chapter_number"]:
                        chapter_found = True
                        chapter_key = ch_data["chapter_number"]
                        chapter_title = ch_data["title"]
                        
                        chapter_content = _get_chapter_content_with_preview(
                            textbook_collection, subject, unit, chapter_key, chapter_title)
                        
                        result["units"][unit]["chapters"][chapter_title] = chapter_content
                        
                        # Add graph data at the unit level if available
                        graph_data = _get_chapter_graph_data(textbook_collection, subject, unit, chapter_key)
                        if graph_data:
                            if "graphs" not in result["units"][unit]:
                                result["units"][unit]["graphs"] = {}
                            result["units"][unit]["graphs"][chapter_key] = graph_data
                
                if not chapter_found:
                    raise ValueError(f"Chapter '{chapter}' not found in Unit {unit}")
            else:
                for ch_data in unit_data["chapters"]:
                    chapter_key = ch_data["chapter_number"]
                    chapter_title = ch_data["title"]
                    
                    chapter_content = _get_chapter_content_with_preview(
                        textbook_collection, subject, unit, chapter_key, chapter_title)
                    
                    result["units"][unit]["chapters"][chapter_title] = chapter_content
                    
                    # Add graph data at the unit level if available  
                    graph_data = _get_chapter_graph_data(textbook_collection, subject, unit, chapter_key)
                    if graph_data:
                        if "graphs" not in result["units"][unit]:
                            result["units"][unit]["graphs"] = {}
                        result["units"][unit]["graphs"][chapter_key] = graph_data
        else:
            for unit_num, unit_data in toc["units"].items():
                from .subject_config import SubjectConfig
                subject_name = SubjectConfig.get_subject_name(subject)
                result["units"][unit_num] = {
                    "title": unit_data["title"],
                    "summary": f"Unit {unit_num}: {unit_data['title']} covers key concepts in {subject_name} including " + 
                              ", ".join([ch["title"] for ch in unit_data["chapters"][:2]]) + 
                              f", and other topics. This unit contains {len(unit_data['chapters'])} chapters."
                }
                
        return result
    
    except Exception as e:
        logger.error(f"Error retrieving textbook content: {str(e)}")
        return {"error": str(e)}

async def generate_textbook_content(subject: str, unit: int, chapter: str) -> List[str]:
    """
    Generate textbook content for a specific chapter using an AI model and store it in MongoDB.
    Content is generated once and then retrieved from the database on subsequent requests.
    
    Args:
        subject: Subject identifier (e.g., "micro", "macro", "biology")
        unit: Unit number
        chapter: Chapter identifier
        
    Returns:
        List of paragraphs with content for the chapter
    """
    from .rag_service import get_rag_response, initialize_vector_store
    from .subject_config import SubjectConfig
    import os
    
    logger.info(f"Getting/generating content for {subject} Unit {unit}, Chapter {chapter}")
    
    from .rag_service import db
    if db is None:
        raise ValueError("MongoDB connection not available")
    
    textbook_collection = db.textbook_content
    
    try:
        chapter_key = chapter
        existing_content = textbook_collection.find_one({"chapter_id": chapter_key})
        
        if existing_content and "content" in existing_content:
            logger.info(f"Found existing content for {chapter_key} in MongoDB")
            return existing_content["content"]
        
        logger.info(f"No existing content found for {chapter_key}, generating new content")
        
        await initialize_vector_store()
        
        toc = await get_textbook_toc(subject)
        subject_config = SubjectConfig.get_subject_config(subject)
        chapter_title = ""
        for ch_data in toc["units"][unit]["chapters"]:
            if chapter == ch_data["chapter_number"] or chapter.lower() in ch_data["title"].lower():
                chapter_title = ch_data["title"]
                break
        
        if not chapter_title:
            raise ValueError(f"Chapter {chapter} not found in unit {unit}")
        
        subject_name = subject_config["name"]
        full_subject_name = subject_config["full_name"]
        prompt = f"""You are helping students learn {full_subject_name}. Provide comprehensive educational content about {chapter_title}.

Create detailed learning material with these sections:

## Introduction
Explain what {chapter_title} means and why it's fundamental to understanding economics. Describe how this topic connects to broader economic principles and real-world decision-making.

## Core Economic Principles
Provide thorough explanations of all key concepts:
- **Term Name** should be bold and followed by comprehensive definitions
- Include multiple real-world examples for each concept
- Explain the economic logic and reasoning behind each principle
- Show how concepts interconnect and build upon each other
- Use current economic events and scenarios to illustrate points

## Theoretical Framework
Explain the academic foundations:
- Historical development of these economic ideas
- Mathematical relationships and formulas where applicable
- Different economic schools of thought and perspectives
- Step-by-step analysis of how economists approach these concepts

## Practical Applications
Demonstrate how these concepts work in reality:
- Current market examples and case studies
- Government policy applications
- Business decision-making scenarios
- Personal finance and individual choice examples
- International economic comparisons

## Economic Analysis and Models
Deep dive into analytical frameworks:
- For any graphical models discussed: explain what each axis represents, the shape and slope of curves/lines, and what different points or areas signify
- Provide detailed explanations of how to interpret and use the models with specific numerical examples
- Describe what causes movements along curves versus shifts of entire curves when applicable
- When discussing economic models that have visual representations, provide thorough explanation first, then mention how they "can be visualized graphically" and add [GRAPH:description] where description briefly describes what the graph should show (e.g., [GRAPH:PPF shift outward due to technology], [GRAPH:supply and demand equilibrium], [GRAPH:elastic vs inelastic demand curves])
- Include step-by-step problem-solving examples showing calculations and interpretations
- Connect models to current economic events and policy debates with real-world data

## Review Questions
Create challenging questions that test understanding:

Question 1: [Conceptual question about key principles]

**Solution:** [Detailed explanation with reasoning]

Question 2: [Application or analytical problem]

**Solution:** [Step-by-step solution with economic interpretation]

## Summary
**Key Takeaways:** Summarize the most important points students should remember, explain practical significance, and connect to other {full_subject_name} topics.

Write 25-35 substantial paragraphs with college-level depth. Each paragraph should be 5-7 sentences with specific examples, current references, and detailed explanations. Cover ALL important subtopics comprehensively.

IMPORTANT: When discussing any economic models, graphs, or analytical tools:
- Dedicate at least 3-4 paragraphs to explaining each major model or concept in detail
- Explain all components, variables, and relationships thoroughly
- Describe visual representations (curves, lines, axes) and what they signify
- Provide multiple concrete examples with specific numbers and calculations
- Explain different scenarios and their implications
- Discuss real-world applications and policy implications
- Include step-by-step analysis and problem-solving approaches

Ensure thorough coverage of each major concept with sufficient depth for AP-level understanding."""
        
        session_id = f"{subject}_{unit}_{chapter}_textbook_gen"
        
        response = await get_rag_response(prompt, session_id, use_history=False)
        
        # Handle new response format (dict with text and optional graph)
        graph_data = None
        if isinstance(response, dict):
            response_text = response.get('text', '')
            graph_data = response.get('graph')
        else:
            response_text = response
            
        # Check if the response contains [GRAPH] markers and generate graphs
        from .graph_response_handler import graph_response_handler
        
        # Split into paragraphs first
        paragraphs = [p.strip() for p in response_text.split('\n\n') if p.strip()]
        
        # Try to use PDF extraction first if available
        use_pdf_extraction = os.getenv('USE_PDF_GRAPH_EXTRACTION', 'false').lower() == 'true'
        
        # Process each paragraph to detect and handle [GRAPH] markers
        graphs_to_generate = []
        processed_paragraphs = []
        
        for i, paragraph in enumerate(paragraphs):
            cleaned_para, should_generate, graph_desc = graph_response_handler.extract_graph_suggestion(paragraph)
            processed_paragraphs.append(cleaned_para)
            
            if should_generate:
                # Find context from surrounding paragraphs
                context_start = max(0, i - 2)
                context_end = min(len(paragraphs), i + 1)
                context_text = ' '.join(paragraphs[context_start:context_end])
                
                # If we have a specific graph description, add it to the context
                if graph_desc:
                    context_text = f"{graph_desc}. {context_text}"
                
                graphs_to_generate.append({
                    'index': i,
                    'context': context_text,
                    'paragraph': cleaned_para,
                    'description': graph_desc
                })
        
        # Generate graphs for each detected [GRAPH] marker
        generated_graphs = {}
        for graph_info in graphs_to_generate:
            try:
                graph_data_item = await graph_response_handler.generate_contextual_graph(
                    graph_info['context'], 
                    f"{chapter_title} - {graph_info['paragraph'][:100]}"
                )
                if graph_data_item:
                    # Store the graph with the paragraph index as key
                    generated_graphs[graph_info['index']] = graph_data_item
                    logger.info(f"Generated {graph_data_item['type']} graph for paragraph {graph_info['index']}")
            except Exception as e:
                logger.error(f"Error generating graph for paragraph {graph_info['index']}: {e}")
        
        # If we have a single main graph from the response, use it
        if graph_data and not generated_graphs:
            generated_graphs['main'] = graph_data
        
        paragraphs = processed_paragraphs
        
        if not paragraphs:
            logger.warning(f"No content generated for {subject} Unit {unit}, Chapter {chapter}")
            paragraphs = [
                f"This chapter covers {chapter_title} within {toc['units'][unit]['title']}.",
                f"It explores key concepts and applications related to {chapter_title}.",
                f"Students will learn about the theoretical frameworks and practical implications of {chapter_title} in {subject}."
            ]
        
        existing_doc = textbook_collection.find_one({"chapter_id": chapter_key})
        if existing_doc:
            logger.info(f"Deleting existing content for {chapter_key} with ID: {existing_doc.get('_id')}")
            textbook_collection.delete_one({"_id": existing_doc.get("_id")})
        
        new_doc = {
            "chapter_id": chapter_key,
            "subject": subject,
            "unit": unit,
            "chapter": chapter,
            "chapter_title": chapter_title,
            "content": paragraphs,
            "generated_at": datetime.datetime.utcnow()
        }
        
        # Include graph data if available
        if generated_graphs:
            # Store multiple graphs with their positions
            new_doc["graphs"] = generated_graphs
            logger.info(f"Stored {len(generated_graphs)} graphs with {chapter_key}")
            for key, graph in generated_graphs.items():
                logger.info(f"  - Graph at position {key}: {graph.get('type', 'unknown')}")
        
        result = textbook_collection.insert_one(new_doc)
        logger.info(f"Inserted new content for {chapter_key} with ID: {result.inserted_id}")
        
        logger.info(f"Successfully generated and stored {len(paragraphs)} paragraphs for {chapter_key}")
        return paragraphs
        
    except Exception as e:
        logger.error(f"Error generating/retrieving content: {str(e)}")
        return [
            f"This chapter covers {chapter} within Unit {unit}.",
            f"Error generating content: {str(e)}",
            f"Please try again later or contact support if the issue persists."
        ]