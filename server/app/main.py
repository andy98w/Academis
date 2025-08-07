from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from .textbook_service import get_textbook_content, get_textbook_toc, generate_textbook_content
from .agent_service import economics_agent
from .subject_config import SubjectConfig
from .graph_service import graph_generator
from .graph_storage import graph_storage
from typing import Optional
import logging
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

app = FastAPI(title="Academis AP Economics API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

background_tasks_set = set()

class QuestionRequest(BaseModel):
    question: str
    session_id: Optional[str] = "default"
    use_history: Optional[bool] = True

class TextbookRequest(BaseModel):
    unit: Optional[int] = None
    chapter: Optional[str] = None

class GenerateTextbookRequest(BaseModel):
    unit: int
    chapter: str

class AnswerResponse(BaseModel):
    answer: str
    session_id: str

async def _subject_endpoint(request: QuestionRequest, subject: str):
    if not SubjectConfig.is_valid_subject(subject):
        raise HTTPException(status_code=400, detail=f"Invalid subject: {subject}")
    
    if not request.question:
        raise HTTPException(status_code=400, detail="Question is required")
    
    try:
        subject_config = SubjectConfig.get_subject_config(subject)
        base_session_id = request.session_id if request.session_id else "default"
        session_id = f"{base_session_id}_{subject}"
        query = f"{subject_config['agent_prefix']} {request.question}"
        answer = await economics_agent.get_response(query, session_id)
        return AnswerResponse(answer=answer, session_id=session_id)
    except Exception as e:
        logger.error(f"Error processing {subject} question: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def _textbook_endpoint(subject: str, unit_id: int = None, chapter: str = None):
    if not SubjectConfig.is_valid_subject(subject):
        raise HTTPException(status_code=400, detail=f"Invalid subject: {subject}")
    
    try:
        result = await get_textbook_content(subject, unit_id, chapter)
        if unit_id and (not result.get("units") or unit_id not in result.get("units", {})):
            subject_name = SubjectConfig.get_subject_name(subject)
            raise HTTPException(status_code=404, detail=f"No content found for {subject_name} unit {unit_id}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        subject_name = SubjectConfig.get_subject_name(subject)
        logger.error(f"Error getting {subject_name} content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def _toc_endpoint(subject: str):
    if not SubjectConfig.is_valid_subject(subject):
        raise HTTPException(status_code=400, detail=f"Invalid subject: {subject}")
    
    try:
        return await get_textbook_toc(subject)
    except Exception as e:
        subject_name = SubjectConfig.get_subject_name(subject)
        logger.error(f"Error getting {subject_name} TOC: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
def health_check():
    return {"status": "ok"}

# Generic subject endpoints
@app.post("/api/{subject}/ask", response_model=AnswerResponse)
async def ask_subject_question(subject: str, request: QuestionRequest):
    return await _subject_endpoint(request, subject)

@app.post("/api/textbook/{subject}", response_model=dict)
async def get_subject_textbook(subject: str, request: TextbookRequest = None):
    if request is None:
        request = TextbookRequest()
    return await _textbook_endpoint(subject, request.unit, request.chapter)

@app.get("/api/textbook/{subject}/units", response_model=dict)
async def get_subject_units(subject: str):
    return await _toc_endpoint(subject)

@app.get("/api/textbook/{subject}/unit/{unit_id}", response_model=dict)
async def get_subject_unit(subject: str, unit_id: int):
    return await _textbook_endpoint(subject, unit_id)

@app.get("/api/textbook/{subject}/unit/{unit_id}/chapter/{chapter}", response_model=dict)
async def get_subject_chapter(subject: str, unit_id: int, chapter: str):
    return await _textbook_endpoint(subject, unit_id, chapter)

@app.get("/api/textbook/{subject}/toc", response_model=dict)
async def get_subject_toc(subject: str):
    return await _toc_endpoint(subject)

@app.post("/api/textbook/generate/{subject}", response_model=dict)
async def generate_subject_content(subject: str, request: GenerateTextbookRequest):
    return await _generate_content_endpoint(subject, request)

# Graph generation endpoints
@app.post("/api/graph/ppf")
async def generate_ppf_graph(request: dict):
    """Generate Production Possibilities Frontier graph"""
    good1 = request.get("good1", "Guns")
    good2 = request.get("good2", "Butter") 
    points = request.get("points")
    
    image_base64 = await graph_generator.generate_ppf_curve(good1, good2, points)
    return {"image": image_base64, "type": "ppf"}

@app.post("/api/graph/supply-demand")
async def generate_supply_demand_graph(request: dict):
    """Generate supply and demand curves"""
    market = request.get("market", "Generic Market")
    eq_price = request.get("equilibrium_price", 10)
    eq_quantity = request.get("equilibrium_quantity", 100)
    
    image_base64 = await graph_generator.generate_supply_demand_curve(market, eq_price, eq_quantity)
    return {"image": image_base64, "type": "supply_demand"}

@app.post("/api/graph/elasticity")
async def generate_elasticity_graph(request: dict):
    """Generate price elasticity visualization"""
    demand_type = request.get("demand_type", "elastic")
    
    image_base64 = await graph_generator.generate_elasticity_graph(demand_type)
    return {"image": image_base64, "type": "elasticity"}

@app.post("/api/graph/custom")
async def generate_custom_graph(request: dict):
    """Generate custom economic graphs from natural language"""
    graph_request = request.get("request", "")
    
    if not graph_request:
        return {"error": "No graph request provided"}
    
    image_base64 = await graph_generator.generate_custom_economic_graph(graph_request)
    return {"image": image_base64, "type": "custom"}

# Graph storage endpoints
@app.get("/api/graph/{graph_id}")
async def get_graph_by_id(graph_id: str):
    """Retrieve stored graph by ID"""
    graph = await graph_storage.get_graph_by_id(graph_id)
    if not graph:
        raise HTTPException(status_code=404, detail="Graph not found")
    return graph

@app.get("/api/graphs")
async def list_graphs(subject: str = None, graph_type: str = None, limit: int = 50):
    """List stored graphs with optional filtering"""
    graphs = await graph_storage.list_graphs(subject, graph_type, limit)
    return {"graphs": graphs, "count": len(graphs)}

@app.delete("/api/graphs/cleanup")
async def cleanup_expired_graphs():
    """Clean up expired graphs"""
    deleted_count = await graph_storage.cleanup_expired_graphs()
    return {"message": f"Cleaned up {deleted_count} expired graphs"}

# Backwards compatibility endpoints (these can be removed later)
@app.post("/api/rag/micro/ask", response_model=AnswerResponse)
async def ask_micro_question(request: QuestionRequest):
    return await _subject_endpoint(request, "micro")

@app.post("/api/rag/macro/ask", response_model=AnswerResponse)
async def ask_macro_question(request: QuestionRequest):
    return await _subject_endpoint(request, "macro")

async def generate_textbook_content_background(subject: str, unit: int, chapter: str):
    try:
        from .rag_service import db
        
        if db is None:
            raise ValueError("MongoDB connection not available")
        
        textbook_collection = db.textbook_content
        chapter_key = f"{subject}_{unit}_{chapter}"
        delete_result = textbook_collection.delete_many({"chapter_id": chapter_key})
        logger.info(f"Deleted {delete_result.deleted_count} existing documents for {chapter_key}")
        
        content = await generate_textbook_content(subject, unit, chapter)
        subject_name = SubjectConfig.get_subject_name(subject)
        logger.info(f"Generated content for {subject_name} Unit {unit}, Chapter {chapter}")
        
    except Exception as e:
        logger.error(f"Error in background generation: {str(e)}")

async def _generate_content_endpoint(subject: str, request: GenerateTextbookRequest):
    if not SubjectConfig.is_valid_subject(subject):
        raise HTTPException(status_code=400, detail=f"Invalid subject: {subject}")
    
    task = asyncio.create_task(
        generate_textbook_content_background(subject, request.unit, request.chapter)
    )
    background_tasks_set.add(task)
    task.add_done_callback(background_tasks_set.discard)
    
    subject_name = SubjectConfig.get_full_subject_name(subject)
    return {
        "message": f"Content generation started for {subject_name} Unit {request.unit}, Chapter {request.chapter}",
        "unit": request.unit,
        "chapter": request.chapter,
        "status": "started"
    }

# Add subjects list endpoint
@app.get("/api/subjects", response_model=dict)
async def get_available_subjects():
    subjects = SubjectConfig.get_available_subjects()
    return {
        "subjects": [
            {
                "id": subject,
                "name": SubjectConfig.get_subject_name(subject),
                "full_name": SubjectConfig.get_full_subject_name(subject),
                "description": SubjectConfig.get_subject_config(subject)["description"]
            }
            for subject in subjects
        ]
    }