
import logging
from typing import Dict, List, Union, Optional
import datetime
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _get_chapter_content_with_preview(textbook_collection, subject: str, unit: int, chapter_key: str, chapter_title: str) -> List[str]:
    """Helper function to get chapter content with conclusion preview"""
    mongo_key = f"{subject}_{unit}_{chapter_key}"
    try:
        mongo_doc = textbook_collection.find_one({"chapter_id": mongo_key})
        
        if mongo_doc and "content" in mongo_doc and mongo_doc["content"]:
            logger.info(f"Found AI-generated content for {mongo_key} in MongoDB")
            content = mongo_doc["content"]
            
            preview_text = "Content not available yet."
            for i, para in enumerate(content):
                if para.strip().lower().startswith('## conclusion'):
                    if i + 1 < len(content) and content[i + 1].strip():
                        conclusion_para = content[i + 1].strip()
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

MICRO_TOC = {
    "type": "micro",
    "units": {
        1: {
            "title": "Basic Economic Concepts",
            "chapters": [
                {"chapter_number": "1.1", "title": "Scarcity and Choice"},
                {"chapter_number": "1.2", "title": "Opportunity Cost and the Production Possibilities Curve"},
                {"chapter_number": "1.3", "title": "Comparative Advantage and Trade"},
                {"chapter_number": "1.4", "title": "Economic Systems"}
            ]
        },
        2: {
            "title": "Supply and Demand",
            "chapters": [
                {"chapter_number": "2.1", "title": "Demand Fundamentals"},
                {"chapter_number": "2.2", "title": "Supply Fundamentals"},
                {"chapter_number": "2.3", "title": "Market Equilibrium and Price Determination"},
                {"chapter_number": "2.4", "title": "Price and Quantity Controls"}
            ]
        },
        3: {
            "title": "Production, Cost, and the Perfect Competition Model",
            "chapters": [
                {"chapter_number": "3.1", "title": "Production and Cost in the Short Run"},
                {"chapter_number": "3.2", "title": "Production and Cost in the Long Run"},
                {"chapter_number": "3.3", "title": "Perfect Competition Market Structure"},
                {"chapter_number": "3.4", "title": "Profit Maximization in Perfectly Competitive Markets"}
            ]
        },
        4: {
            "title": "Imperfect Competition",
            "chapters": [
                {"chapter_number": "4.1", "title": "Monopoly Market Structure"},
                {"chapter_number": "4.2", "title": "Price Discrimination"},
                {"chapter_number": "4.3", "title": "Monopolistic Competition"},
                {"chapter_number": "4.4", "title": "Oligopoly and Game Theory"}
            ]
        },
        5: {
            "title": "Factor Markets",
            "chapters": [
                {"chapter_number": "5.1", "title": "Derived Factor Demand"},
                {"chapter_number": "5.2", "title": "Marginal Revenue Product"},
                {"chapter_number": "5.3", "title": "Labor Market and Wages"},
                {"chapter_number": "5.4", "title": "Interest Rates and Capital Markets"}
            ]
        },
        6: {
            "title": "Market Failure and the Role of Government",
            "chapters": [
                {"chapter_number": "6.1", "title": "Externalities and Public Goods"},
                {"chapter_number": "6.2", "title": "Public Policy to Address Externalities"},
                {"chapter_number": "6.3", "title": "Income Distribution and Equity"},
                {"chapter_number": "6.4", "title": "Government Intervention in Markets"}
            ]
        }
    }
}

MACRO_TOC = {
    "type": "macro",
    "units": {
        1: {
            "title": "Basic Economic Concepts",
            "chapters": [
                {"chapter_number": "1.1", "title": "Scarcity and Choice in Macroeconomics"},
                {"chapter_number": "1.2", "title": "Production Possibilities and Opportunity Cost"},
                {"chapter_number": "1.3", "title": "Comparative Advantage and Trade"},
                {"chapter_number": "1.4", "title": "Economic Systems and Macroeconomic Objectives"}
            ]
        },
        2: {
            "title": "Economic Indicators and the Business Cycle",
            "chapters": [
                {"chapter_number": "2.1", "title": "Measuring GDP and National Income"},
                {"chapter_number": "2.2", "title": "Unemployment and Inflation"},
                {"chapter_number": "2.3", "title": "Business Cycles"},
                {"chapter_number": "2.4", "title": "Economic Growth and Economic Development"}
            ]
        },
        3: {
            "title": "National Income and Price Determination",
            "chapters": [
                {"chapter_number": "3.1", "title": "Aggregate Demand"},
                {"chapter_number": "3.2", "title": "Aggregate Supply"},
                {"chapter_number": "3.3", "title": "Macroeconomic Equilibrium"},
                {"chapter_number": "3.4", "title": "Fiscal Policy and Economic Stability"}
            ]
        },
        4: {
            "title": "Financial Sector",
            "chapters": [
                {"chapter_number": "4.1", "title": "Money, Banking, and Financial Markets"},
                {"chapter_number": "4.2", "title": "Monetary Policy"},
                {"chapter_number": "4.3", "title": "The Money Market"},
                {"chapter_number": "4.4", "title": "The Loanable Funds Market"}
            ]
        },
        5: {
            "title": "Long-Run Consequences of Stabilization Policies",
            "chapters": [
                {"chapter_number": "5.1", "title": "Fiscal and Monetary Policy Actions"},
                {"chapter_number": "5.2", "title": "Government Deficits and the National Debt"},
                {"chapter_number": "5.3", "title": "Crowding Out and Economic Growth"},
                {"chapter_number": "5.4", "title": "Policy Debates and Economic Schools of Thought"}
            ]
        },
        6: {
            "title": "Open Economy—International Trade and Finance",
            "chapters": [
                {"chapter_number": "6.1", "title": "Balance of Payments Accounts"},
                {"chapter_number": "6.2", "title": "Exchange Rates and International Capital Flows"},
                {"chapter_number": "6.3", "title": "Effects of Changes in Trade and Capital Flows"},
                {"chapter_number": "6.4", "title": "Trade Restrictions and Trade Agreements"}
            ]
        }
    }
}

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
        from .subject_config import SubjectConfig
        subject_config = SubjectConfig.get_subject_config(subject)
        toc = subject_config["toc"]
        
        if toc is None:
            # For future subjects, load TOC from database or file
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
                        
                        result["units"][unit]["chapters"][chapter_title] = _get_chapter_content_with_preview(
                            textbook_collection, subject, unit, chapter_key, chapter_title)
                
                if not chapter_found:
                    raise ValueError(f"Chapter '{chapter}' not found in Unit {unit}")
            else:
                for ch_data in unit_data["chapters"]:
                    chapter_key = ch_data["chapter_number"]
                    chapter_title = ch_data["title"]
                    
                    result["units"][unit]["chapters"][chapter_title] = _get_chapter_content_with_preview(
                        textbook_collection, subject, unit, chapter_key, chapter_title)
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
        chapter_key = f"{subject}_{unit}_{chapter}"
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
        prompt = f"""Create comprehensive, in-depth textbook content for {full_subject_name} on the topic: {chapter_title}.
        
        This content MUST:
        1. Be suitable for an {full_subject_name} textbook with COLLEGE-LEVEL depth and breadth
        2. Include extremely thorough definitions of ALL key concepts with multiple aspects and nuances explained
        3. Provide detailed theoretical explanations with mathematical formulas, equations, and academic-level analysis
        4. Include MANY real-world examples, case studies, current economic scenarios, and news references
        5. Present content in a logical progression of ideas with proper transitions between subtopics
        6. Be comprehensive (15-20 substantial paragraphs MINIMUM) with LENGTHY, DETAILED explanations
        7. Include example problems WITHIN relevant sections to illustrate concepts as they are explained
        8. Include 2-4 challenging review questions as a separate section at the end (MINIMUM 2 review questions)
        9. Include DETAILED descriptions of relevant graphs, tables, and charts, explaining all axes, curves, intersections, and economic interpretations
        10. Reference concepts from standard AP Economics textbooks, academic sources, and economic research
        11. Cover ALL important subtopics related to {chapter_title} in exhaustive detail
        12. Include critical analysis and different perspectives where appropriate
        13. Add historical context and development of key economic theories
        
        FORMATTING REQUIREMENTS:
        1. Use a single string for the entire content, with formatting markers
        2. ALWAYS start with '## Introduction' section that provides an overview of the chapter topics and their importance
        3. Use '## ' to indicate major section headings (e.g., '## Key Concepts', '## Applications')
        4. Use '**Bold Term**' (without colon) to highlight key terms at the beginning of their paragraphs
        5. DO NOT use subheadings like "Explanation" - integrate explanations directly into paragraphs
        6. Each key concept should be presented as: "**Term** refers to/is/means... [definition and explanation with integrated examples]"
        7. Use '---' to create horizontal rules between major sections
        8. Use bullet points ('* ') for listing items where appropriate
        9. Include detailed graph descriptions directly within paragraphs. 
           Do NOT use separate "Graph:" sections. Instead, explain graphs in the flow of the regular text,
           giving detailed descriptions of all axes, curves, intersections, and relationships within the 
           regular paragraphs that explain the concepts.
        10. For example problems within sections, format them as:
            "For example, consider the following scenario:" followed by the example problem
            and its solution in the same paragraph
        11. Format review questions EXACTLY as shown in this example:
            '## Review Questions'
            'Question 1: What is the law of demand?'
            '**Solution:** The law of demand states that...'
            'Question 2: Calculate the price elasticity...'
            '**Solution:** To calculate the price elasticity...'
            
            IMPORTANT: For each question's solution, always start on a new line with EXACTLY '**Solution:**' 
            followed by a space and then the solution text. Do not use "Solution to Question X:" format.
        12. ALWAYS include a '## Conclusion' section at the end (before the Review Questions) that summarizes key takeaways, practical implications, and bridges to related topics

        For graphs and visual elements, provide extremely detailed text descriptions integrated directly into paragraphs. Explain what each graph would show, including axes labels, curves, points of interest, shifts, movements, and economic interpretations. Include descriptions of ALL standard graphs used in AP Economics textbooks for this topic, but do not create separate graph sections - keep all explanations flowing within the regular text.
        
        The content should be comprehensive enough to serve as a complete learning resource for students studying for the {full_subject_name} exam."""
        
        session_id = f"{subject}_{unit}_{chapter}_textbook_gen"
        
        response = await get_rag_response(prompt, session_id, use_history=False)
        
        paragraphs = [p.strip() for p in response.split('\n\n') if p.strip()]
        
        if not paragraphs:
            logger.warning(f"No content generated for {economics_type} Unit {unit}, Chapter {chapter}")
            paragraphs = [
                f"This chapter covers {chapter_title} within {toc['units'][unit]['title']}.",
                f"It explores key concepts and applications related to {chapter_title}.",
                f"Students will learn about the theoretical frameworks and practical implications of {chapter_title} in {economics_type}economics."
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