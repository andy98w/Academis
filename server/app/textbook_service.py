
import logging
from typing import List
import datetime
import os
from dotenv import load_dotenv

load_dotenv(override=True)
from .helpers import (
    load_toc_from_file,
    get_chapter_data,
    validate_and_clean_content
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def get_textbook_toc(subject: str) -> dict:
    try:
        toc = load_toc_from_file(subject)
        if toc:
            return toc
        from .subject_config import SubjectConfig
        subject_config = SubjectConfig.get_subject_config(subject)
        return subject_config.get("toc", {"type": subject, "units": {}})
    
    except Exception as e:
        logger.error(f"Error getting textbook TOC: {str(e)}")
        return {"error": str(e)}

async def get_textbook_content(subject: str, unit: int = None, chapter: str = None) -> dict:
    try:
        from .rag_service import db
        if db is None:
            raise ValueError("MongoDB connection not available")
        
        textbook_collection = db.textbook_content
        toc = await get_textbook_toc(subject)
        result = {"type": subject, "units": {}}
        
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

                        chapter_content, graph_data, quiz_data = get_chapter_data(
                            textbook_collection, subject, unit, chapter_key, chapter_title)
                        result["units"][unit]["chapters"][chapter_title] = chapter_content
                        if graph_data:
                            if "graphs" not in result["units"][unit]:
                                result["units"][unit]["graphs"] = {}
                            result["units"][unit]["graphs"][chapter_key] = graph_data
                        if quiz_data:
                            if "quiz" not in result["units"][unit]:
                                result["units"][unit]["quiz"] = {}
                            result["units"][unit]["quiz"][chapter_key] = quiz_data

                if not chapter_found:
                    raise ValueError(f"Chapter '{chapter}' not found in Unit {unit}")
            else:
                for ch_data in unit_data["chapters"]:
                    chapter_key = ch_data["chapter_number"]
                    chapter_title = ch_data["title"]

                    chapter_content, graph_data, quiz_data = get_chapter_data(
                        textbook_collection, subject, unit, chapter_key, chapter_title)
                    result["units"][unit]["chapters"][chapter_title] = chapter_content
                    if graph_data:
                        if "graphs" not in result["units"][unit]:
                            result["units"][unit]["graphs"] = {}
                        result["units"][unit]["graphs"][chapter_key] = graph_data
                    if quiz_data:
                        if "quiz" not in result["units"][unit]:
                            result["units"][unit]["quiz"] = {}
                        result["units"][unit]["quiz"][chapter_key] = quiz_data
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
    from .subject_config import SubjectConfig
    
    logger.info(f"Getting/generating content for {subject} Unit {unit}, Chapter {chapter}")
    
    from .rag_service import db
    if db is None:
        raise ValueError("MongoDB connection not available")
    
    textbook_collection = db.textbook_content
    
    try:
        # Get chapter information that both paths need
        toc = await get_textbook_toc(subject)
        subject_config = SubjectConfig.get_subject_config(subject)
        chapter_title = ""
        chapter_key = chapter  # Will be updated to chapter_number if found
        for ch_data in toc["units"][unit]["chapters"]:
            if chapter == ch_data["chapter_number"] or chapter.lower() in ch_data["title"].lower():
                chapter_title = ch_data["title"]
                chapter_key = ch_data["chapter_number"]  # Use chapter number as key
                break

        if not chapter_title:
            raise ValueError(f"Chapter {chapter} not found in unit {unit}")

        # Check for and delete any existing content to ensure fresh generation
        existing_content = textbook_collection.find_one({"chapter_id": chapter_key, "subject": subject})

        if existing_content:
            logger.info(f"Found existing content for {chapter_key}, deleting to generate fresh content")
            textbook_collection.delete_one({"_id": existing_content["_id"]})

        logger.info(f"Generating fresh content for {chapter_key}")
        
        full_subject_name = subject_config["full_name"]

        # Check if agentic generator is enabled
        use_agentic = os.getenv('USE_AGENTIC_GENERATOR', 'false').lower() == 'true'

        if use_agentic:
            # --- Agentic path: agent handles tools, graphs, and tables ---
            logger.info(f"Using AGENTIC textbook generation for {chapter_title}")
            from .agentic_textbook_generator import agentic_generator

            paragraphs, generated_graphs = await agentic_generator.generate_chapter(
                full_subject_name, chapter, chapter_title, subject
            )

            # Validate and clean content
            paragraphs = validate_and_clean_content(paragraphs, subject, unit, chapter, toc)

            new_doc = {
                "chapter_id": chapter_key,
                "subject": subject,
                "unit": unit,
                "chapter": chapter,
                "chapter_title": chapter_title,
                "content": paragraphs,
                "generated_at": datetime.datetime.now(datetime.timezone.utc)
            }

            if generated_graphs:
                cleaned_graphs = {}
                for key, graph in generated_graphs.items():
                    try:
                        str_key = str(key)
                        if isinstance(graph, dict) and 'type' in graph:
                            cleaned = {
                                'type': str(graph.get('type', 'unknown')),
                                'title': str(graph.get('title', '')),
                                'description': str(graph.get('description', ''))
                            }
                            # Graphs have base64 image data
                            if graph.get('image'):
                                cleaned['image'] = str(graph['image'])
                            # Tables have structured column/row data
                            if graph.get('columns'):
                                cleaned['columns'] = graph['columns']
                            if graph.get('rows'):
                                cleaned['rows'] = graph['rows']
                            cleaned_graphs[str_key] = cleaned
                            logger.info(f"  - Asset at position {key}: {graph.get('title', 'unknown')} (type={cleaned['type']})")
                    except Exception as graph_error:
                        logger.warning(f"Skipping invalid asset at position {key}: {graph_error}")

                if cleaned_graphs:
                    new_doc["graphs"] = cleaned_graphs
                    logger.info(f"Stored {len(cleaned_graphs)} assets with {chapter_key}")

            # Generate quiz questions for this chapter
            try:
                from .quiz_generator import quiz_generator

                logger.info(f"Generating quiz for {chapter_key}")
                quiz_questions = await quiz_generator.generate_quiz(
                    subject=full_subject_name,
                    chapter_content=paragraphs,
                    chapter_title=chapter_title,
                    num_questions=5
                )

                if quiz_questions:
                    new_doc["quiz"] = quiz_questions
                    logger.info(f"Generated {len(quiz_questions)} quiz questions for {chapter_key}")
            except Exception as quiz_error:
                logger.warning(f"Failed to generate quiz for {chapter_key}: {quiz_error}")

            result = textbook_collection.insert_one(new_doc)
            logger.info(f"Inserted agentic content for {chapter_key} with ID: {result.inserted_id}")
            logger.info(f"Successfully generated {len(paragraphs)} paragraphs for {chapter_key}")
            return paragraphs

        # --- Legacy pipeline path (unchanged) ---
        from .textbook_agent import textbook_agent

        logger.info(f"Using enhanced textbook generation for {chapter_title}")
        use_web_search = os.getenv('TAVILY_API_KEY') is not None

        response_text = await textbook_agent.generate_enhanced_textbook_content(
            full_subject_name,
            f"{chapter}: {chapter_title}",
            use_web_search=use_web_search,
            subject_code=subject  # Pass subject code for topic lookup
        )
        
        # Join paragraphs if they're already a list
        if isinstance(response_text, list):
            paragraphs = response_text
        else:
            paragraphs = [p.strip() for p in response_text.split('\n\n') if p.strip()]
            
        # Initialize graph_data for both paths
        graph_data = None
        
        # Check if the response contains [GRAPH] markers and generate graphs
        from .graph_response_handler import graph_response_handler
        
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
                    'description': graph_desc,
                    'chapter_title': chapter_title
                })
        
        # Generate graphs, but deduplicate by core concept to avoid near-identical visuals
        generated_graphs = {}
        seen_concepts = set()
        for graph_info in graphs_to_generate:
            try:
                full_context = f"Chapter: {chapter_title}\n\n{graph_info['context']}"
                graph_data_item = await graph_response_handler.generate_contextual_graph(
                    full_context,
                    f"{chapter_title} - {graph_info['paragraph'][:100]}"
                )
                if graph_data_item:
                    # Extract a normalized concept key from the graph type/title
                    graph_type = graph_data_item.get("type", "").lower()
                    graph_title = graph_data_item.get("title", "").lower()
                    combined = f"{graph_type} {graph_title}"

                    # Extract core concept by removing common filler words
                    import re
                    concept_key = re.sub(r'\b(the|a|an|in|of|and|with|for|to|vs|versus)\b', '', combined)
                    concept_key = re.sub(r'[^a-z]+', ' ', concept_key).strip()
                    # Take first 3 significant words as the concept fingerprint
                    words = [w for w in concept_key.split() if len(w) > 2][:3]
                    concept_key = ' '.join(sorted(words))

                    if concept_key not in seen_concepts:
                        seen_concepts.add(concept_key)
                        graph_key = str(graph_info['index'])
                        generated_graphs[graph_key] = graph_data_item
                        logger.info(f"Generated graph '{graph_data_item['type']}' (concept: {concept_key}) for paragraph {graph_info['index']}")
                    else:
                        logger.info(f"Skipping duplicate concept '{concept_key}' for paragraph {graph_info['index']}")
            except Exception as e:
                logger.error(f"Error generating graph for paragraph {graph_info['index']}: {e}")
        
        # If we have a single main graph from the response, use it
        if graph_data and not generated_graphs:
            generated_graphs['main'] = graph_data
        
        paragraphs = processed_paragraphs
        
        # Validate and clean content to ensure MongoDB compatibility
        paragraphs = validate_and_clean_content(paragraphs, subject, unit, chapter, toc)
        
        
        new_doc = {
            "chapter_id": chapter_key,
            "subject": subject,
            "unit": unit,
            "chapter": chapter,
            "chapter_title": chapter_title,
            "content": paragraphs,
            "generated_at": datetime.datetime.now(datetime.timezone.utc)
        }
        
        # Include graph data if available
        if generated_graphs:
            # Validate and clean graph data to ensure MongoDB compatibility
            cleaned_graphs = {}
            for key, graph in generated_graphs.items():
                try:
                    # Ensure key is a string and graph is a proper dict
                    str_key = str(key)
                    if isinstance(graph, dict) and 'type' in graph:
                        cleaned_graphs[str_key] = {
                            'type': str(graph.get('type', 'unknown')),
                            'image': str(graph.get('image', '')),
                            'title': str(graph.get('title', '')),
                            'description': str(graph.get('description', ''))
                        }
                    logger.info(f"  - Graph at position {key}: {graph.get('type', 'unknown')}")
                except Exception as graph_error:
                    logger.warning(f"Skipping invalid graph at position {key}: {graph_error}")
            
            # Only add graphs if we have valid ones
            if cleaned_graphs:
                new_doc["graphs"] = cleaned_graphs
                logger.info(f"Stored {len(cleaned_graphs)} graphs with {chapter_key}")
            else:
                logger.warning(f"No valid graphs to store for {chapter_key}")
        
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

