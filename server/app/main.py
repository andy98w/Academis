from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from .rag_service import get_rag_response
from .textbook_service import get_textbook_content, get_textbook_toc, generate_textbook_content
from .agent_service import economics_agent
from typing import Optional
import logging
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI(title="Academis AP Economics API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store background tasks to keep them from being garbage collected
background_tasks_set = set()

class QuestionRequest(BaseModel):
    question: str
    session_id: Optional[str] = "default"
    use_history: Optional[bool] = True

class AnswerResponse(BaseModel):
    answer: str
    session_id: str
    
class TextbookRequest(BaseModel):
    unit: Optional[int] = None
    chapter: Optional[str] = None
    
class GenerateTextbookRequest(BaseModel):
    unit: int
    chapter: str

@app.get("/api/health")
def health_check():
    return {"status": "ok"}

@app.post("/api/rag/micro/ask", response_model=AnswerResponse)
async def ask_micro_question(request: QuestionRequest):
    """Endpoint for microeconomics questions"""
    if not request.question:
        raise HTTPException(status_code=400, detail="Question is required")
    
    try:
        base_session_id = request.session_id if request.session_id else "default"
        session_id = f"{base_session_id}_micro"
        
        query = f"[Microeconomics Question] {request.question}"
        
        answer = await economics_agent.get_response(query, session_id)
        
        return AnswerResponse(
            answer=answer, 
            session_id=session_id
        )
    except Exception as e:
        logger.error(f"Error processing micro question: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/rag/macro/ask", response_model=AnswerResponse)
async def ask_macro_question(request: QuestionRequest):
    """Endpoint for macroeconomics questions"""
    if not request.question:
        raise HTTPException(status_code=400, detail="Question is required")
    
    try:
        base_session_id = request.session_id if request.session_id else "default"
        session_id = f"{base_session_id}_macro"
        
        query = f"[Macroeconomics Question] {request.question}"
        
        answer = await economics_agent.get_response(query, session_id)
        
        return AnswerResponse(
            answer=answer, 
            session_id=session_id
        )
    except Exception as e:
        logger.error(f"Error processing macro question: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/textbook/micro", response_model=dict)
async def get_micro_textbook(request: TextbookRequest = None):
    """Get microeconomics textbook content organized by units and chapters"""
    if request is None:
        request = TextbookRequest()
        
    try:
        result = await get_textbook_content("micro", request.unit, request.chapter)
        return result
    except Exception as e:
        logger.error(f"Error getting microeconomics textbook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/textbook/macro", response_model=dict)
async def get_macro_textbook(request: TextbookRequest = None):
    """Get macroeconomics textbook content organized by units and chapters"""
    if request is None:
        request = TextbookRequest()
        
    try:
        result = await get_textbook_content("macro", request.unit, request.chapter)
        return result
    except Exception as e:
        logger.error(f"Error getting macroeconomics textbook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/textbook/micro/units", response_model=dict)
async def get_micro_units():
    """Get a list of microeconomics units"""
    return {
        "units": {
            1: "Basic Economic Concepts",
            2: "Supply and Demand",
            3: "Production, Cost, and the Perfect Competition Model",
            4: "Imperfect Competition",
            5: "Factor Markets",
            6: "Market Failure and the Role of Government",
            7: "Consumer Choice and Elasticity",
            8: "Firm Behavior and Market Structure",
            9: "Market Efficiency and Equity"
        }
    }

@app.get("/api/textbook/macro/units", response_model=dict)
async def get_macro_units():
    """Get a list of macroeconomics units"""
    return {
        "units": {
            1: "Basic Economic Concepts",
            2: "Economic Indicators and the Business Cycle",
            3: "National Income and Price Determination",
            4: "Financial Sector",
            5: "Long-Run Consequences of Stabilization Policies",
            6: "Open Economy—International Trade and Finance"
        }
    }

@app.get("/api/textbook/micro/unit/{unit_id}", response_model=dict)
async def get_micro_unit(unit_id: int):
    """Get content for a specific microeconomics unit"""
    try:
        result = await get_textbook_content("micro", unit=unit_id)
        
        # If no content was found for this unit
        if not result.get("units") or unit_id not in result.get("units", {}):
            raise HTTPException(status_code=404, detail=f"No content found for microeconomics unit {unit_id}")
            
        return result
    except Exception as e:
        logger.error(f"Error getting microeconomics unit content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/textbook/macro/unit/{unit_id}", response_model=dict)
async def get_macro_unit(unit_id: int):
    """Get content for a specific macroeconomics unit"""
    try:
        result = await get_textbook_content("macro", unit=unit_id)
        
        # If no content was found for this unit
        if not result.get("units") or unit_id not in result.get("units", {}):
            raise HTTPException(status_code=404, detail=f"No content found for macroeconomics unit {unit_id}")
            
        return result
    except Exception as e:
        logger.error(f"Error getting macroeconomics unit content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/textbook/micro/unit/{unit_id}/chapter/{chapter}", response_model=dict)
async def get_micro_chapter(unit_id: int, chapter: str):
    """Get content for a specific chapter in a microeconomics unit"""
    try:
        result = await get_textbook_content("micro", unit=unit_id, chapter=chapter)
        
        # Check if any matching chapters were found
        if not result.get("units") or unit_id not in result.get("units", {}) or not result["units"][unit_id].get("chapters"):
            raise HTTPException(status_code=404, detail=f"No content found for chapter '{chapter}' in microeconomics unit {unit_id}")
            
        return result
    except Exception as e:
        logger.error(f"Error getting microeconomics chapter content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/textbook/macro/unit/{unit_id}/chapter/{chapter}", response_model=dict)
async def get_macro_chapter(unit_id: int, chapter: str):
    """Get content for a specific chapter in a macroeconomics unit"""
    try:
        result = await get_textbook_content("macro", unit=unit_id, chapter=chapter)
        
        # Check if any matching chapters were found
        if not result.get("units") or unit_id not in result.get("units", {}) or not result["units"][unit_id].get("chapters"):
            raise HTTPException(status_code=404, detail=f"No content found for chapter '{chapter}' in macroeconomics unit {unit_id}")
            
        return result
    except Exception as e:
        logger.error(f"Error getting macroeconomics chapter content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
        
@app.get("/api/textbook/micro/toc", response_model=dict)
async def get_micro_toc():
    """Get the table of contents for the microeconomics textbook"""
    try:
        result = await get_textbook_toc("micro")
        return result
    except Exception as e:
        logger.error(f"Error getting microeconomics TOC: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
        
@app.get("/api/textbook/macro/toc", response_model=dict)
async def get_macro_toc():
    """Get the table of contents for the macroeconomics textbook"""
    try:
        result = await get_textbook_toc("macro")
        return result
    except Exception as e:
        logger.error(f"Error getting macroeconomics TOC: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
        
async def generate_textbook_content_background(economics_type: str, unit: int, chapter: str):
    try:
        from pymongo import MongoClient
        from pymongo.server_api import ServerApi
        import os
        import datetime
        
        uri = os.getenv("MONGODB_URI")
        if not uri:
            raise ValueError("MONGODB_URI environment variable is not set")
        
        client = MongoClient(uri, server_api=ServerApi('1'))
        db = client.Academis
        textbook_collection = db.textbook_content
        
        chapter_key = f"{economics_type}_{unit}_{chapter}"
        delete_result = textbook_collection.delete_many({"chapter_id": chapter_key})
        logger.info(f"Deleted {delete_result.deleted_count} existing documents for {chapter_key}")
        
        from .rag_service import get_rag_response, initialize_vector_store
        from .textbook_service import get_textbook_toc
        
        await initialize_vector_store()
        
        toc = await get_textbook_toc(economics_type)
        chapter_title = ""
        for ch_data in toc["units"][unit]["chapters"]:
            if chapter == ch_data["chapter_number"] or chapter.lower() in ch_data["title"].lower():
                chapter_title = ch_data["title"]
                break
        
        if not chapter_title:
            raise ValueError(f"Chapter {chapter} not found in unit {unit}")
        prompt = f"""Create comprehensive, in-depth textbook content for {economics_type}economics on the topic: {chapter_title}.
        
        This content MUST:
        1. Be suitable for an AP {economics_type.capitalize()}economics textbook with COLLEGE-LEVEL depth and breadth
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
        
        The content should be comprehensive enough to serve as a complete learning resource for students studying for the AP {economics_type.capitalize()}economics exam."""
        
        session_id = f"{economics_type}_{unit}_{chapter}_textbook_gen_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        from langchain_openai import ChatOpenAI
        from langchain.prompts import ChatPromptTemplate
        from langchain.schema.output_parser import StrOutputParser
        
        gpt4_model = ChatOpenAI(model_name="gpt-4", temperature=0.2)
        prompt_template = ChatPromptTemplate.from_template(prompt)
        chain = prompt_template | gpt4_model | StrOutputParser()
        logger.info("Generating content with GPT-4 model for higher quality")
        response = await chain.ainvoke({})
        
        paragraphs = [p.strip() for p in response.split('\n\n') if p.strip()]
        new_doc = {
            "chapter_id": chapter_key,
            "economics_type": economics_type,
            "unit": unit,
            "chapter": chapter,
            "chapter_title": chapter_title,
            "content": paragraphs,
            "generated_at": datetime.datetime.utcnow()
        }
        
        result = textbook_collection.insert_one(new_doc)
        logger.info(f"Successfully regenerated and stored {len(paragraphs)} paragraphs for {chapter_key}")
        
    except Exception as e:
        logger.error(f"Error in background generation for {economics_type} Unit {unit}, Chapter {chapter}: {str(e)}")
    
@app.post("/api/textbook/generate/micro", response_model=dict)
async def generate_micro_content(request: GenerateTextbookRequest):
    """Generate new content for a microeconomics chapter and store in MongoDB"""
    try:
        # Create background task
        background_task = asyncio.create_task(
            generate_textbook_content_background("micro", request.unit, request.chapter)
        )
        
        # Add to background tasks set to prevent garbage collection
        background_tasks_set.add(background_task)
        # Add a callback to remove the task when done
        background_task.add_done_callback(lambda t: background_tasks_set.discard(t))
        
        return {
            "status": "processing",
            "message": f"Content generation for Microeconomics Unit {request.unit}, Chapter {request.chapter} has been started in the background.",
            "economics_type": "micro",
            "unit": request.unit,
            "chapter": request.chapter
        }
    except Exception as e:
        logger.error(f"Error starting content generation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
        
@app.post("/api/textbook/generate/macro", response_model=dict)
async def generate_macro_content(request: GenerateTextbookRequest):
    """Generate new content for a macroeconomics chapter and store in MongoDB"""
    try:
        # Create background task
        background_task = asyncio.create_task(
            generate_textbook_content_background("macro", request.unit, request.chapter)
        )
        
        # Add to background tasks set to prevent garbage collection
        background_tasks_set.add(background_task)
        # Add a callback to remove the task when done
        background_task.add_done_callback(lambda t: background_tasks_set.discard(t))
        
        return {
            "status": "processing",
            "message": f"Content generation for Macroeconomics Unit {request.unit}, Chapter {request.chapter} has been started in the background.",
            "economics_type": "macro",
            "unit": request.unit,
            "chapter": request.chapter
        }
    except Exception as e:
        logger.error(f"Error starting content generation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8080, reload=True)