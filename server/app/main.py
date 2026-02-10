from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from .textbook_service import get_textbook_content, get_textbook_toc, generate_textbook_content
from .agent_service import get_agent
from .subject_config import SubjectConfig
from .graph_storage import graph_storage
from typing import Optional
import logging
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv(override=True)

app = FastAPI(title="Academis Multi-Subject AP API")
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

class GenerateQuizRequest(BaseModel):
    unit: int
    chapter: str
    num_questions: Optional[int] = 5

class AnswerResponse(BaseModel):
    answer: str
    session_id: str

async def _subject_endpoint(request: QuestionRequest, subject: str):
    if not SubjectConfig.is_valid_subject(subject):
        raise HTTPException(status_code=400, detail=f"Invalid subject: {subject}")

    if not request.question:
        raise HTTPException(status_code=400, detail="Question is required")

    try:
        base_session_id = request.session_id if request.session_id else "default"
        session_id = f"{base_session_id}_{subject}"

        # Get the appropriate agent for this subject
        agent = get_agent(subject)
        answer = await agent.get_response(request.question, session_id)

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

# Graph generation endpoint - Universal system replaces hardcoded types

@app.post("/api/graph/universal")
async def generate_universal_graph(request: dict):
    """Generate graphs universally based on content analysis - no hardcoded types"""
    content = request.get("content", "")
    title = request.get("title", "")
    
    if not content:
        return {"error": "No content provided for analysis"}
    
    from .graph_service import universal_graph_generator
    
    result = await universal_graph_generator.generate_contextual_graph(content, title)
    
    if not result:
        return {"message": "No visualization needed for this content", "graph_generated": False}
    
    return {
        "graph_generated": True,
        "type": result["type"],
        "image": result["image"],
        "title": result["title"],
        "description": result["description"]
    }

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

# Quiz endpoints
@app.post("/api/quiz/generate/{subject}", response_model=dict)
async def generate_quiz(subject: str, request: GenerateQuizRequest):
    """Generate a practice quiz for a chapter"""
    if not SubjectConfig.is_valid_subject(subject):
        raise HTTPException(status_code=400, detail=f"Invalid subject: {subject}")

    try:
        from .quiz_generator import quiz_generator
        from .textbook_service import get_textbook_toc
        from .helpers import get_chapter_data, load_chapter_topics
        from .rag_service import db

        if db is None:
            raise HTTPException(status_code=500, detail="Database not available")

        # Get TOC to find chapter info
        toc = await get_textbook_toc(subject)
        chapter_title = ""
        chapter_key = request.chapter

        for ch_data in toc["units"].get(request.unit, {}).get("chapters", []):
            if request.chapter == ch_data["chapter_number"] or request.chapter.lower() in ch_data["title"].lower():
                chapter_title = ch_data["title"]
                chapter_key = ch_data["chapter_number"]
                break

        if not chapter_title:
            raise HTTPException(status_code=404, detail=f"Chapter {request.chapter} not found")

        # Get chapter content
        textbook_collection = db.textbook_content
        content, _ = get_chapter_data(textbook_collection, subject, request.unit, chapter_key, chapter_title)

        # Get topics
        topics_data = load_chapter_topics(subject)
        topics = topics_data.get(chapter_key, [])

        # Generate quiz
        subject_name = SubjectConfig.get_full_subject_name(subject)
        questions = await quiz_generator.generate_quiz(
            subject=subject_name,
            chapter_content=content,
            topics=topics,
            num_questions=request.num_questions
        )

        # Store quiz in database
        quiz_collection = db.quiz_questions
        quiz_doc = {
            "subject": subject,
            "unit": request.unit,
            "chapter_id": chapter_key,
            "chapter_title": chapter_title,
            "questions": questions,
            "generated_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
        }

        # Update or insert
        quiz_collection.update_one(
            {"subject": subject, "chapter_id": chapter_key},
            {"$set": quiz_doc},
            upsert=True
        )

        logger.info(f"Generated {len(questions)} quiz questions for {subject} {chapter_key}")

        return {
            "message": f"Quiz generated for {chapter_title}",
            "chapter_id": chapter_key,
            "num_questions": len(questions),
            "questions": questions
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating quiz: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/quiz/{subject}/all", response_model=dict)
async def get_all_quizzes(subject: str):
    """Get all quiz questions for a subject (from all chapters)"""
    if not SubjectConfig.is_valid_subject(subject):
        raise HTTPException(status_code=400, detail=f"Invalid subject: {subject}")

    try:
        from .rag_service import db
        from .textbook_service import get_textbook_toc

        if db is None:
            raise HTTPException(status_code=500, detail="Database not available")

        # Get TOC for chapter titles
        toc = await get_textbook_toc(subject)

        # Get all chapters with quizzes
        textbook_collection = db.textbook_content
        chapters_with_quiz = textbook_collection.find(
            {"subject": subject, "quiz": {"$exists": True, "$ne": []}},
            {"chapter_id": 1, "chapter_title": 1, "unit": 1, "quiz": 1, "_id": 0}
        )

        all_questions = []
        for doc in chapters_with_quiz:
            chapter_id = doc.get("chapter_id", "")
            chapter_title = doc.get("chapter_title", "")
            unit = doc.get("unit", 0)
            unit_title = toc.get("units", {}).get(unit, {}).get("title", f"Unit {unit}")

            for q in doc.get("quiz", []):
                q["chapter_id"] = chapter_id
                q["chapter_title"] = chapter_title
                q["unit"] = unit
                q["unit_title"] = unit_title
                all_questions.append(q)

        return {
            "subject": subject,
            "total_questions": len(all_questions),
            "questions": all_questions
        }

    except Exception as e:
        logger.error(f"Error getting all quizzes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/quiz/{subject}/{chapter_id}", response_model=dict)
async def get_quiz(subject: str, chapter_id: str):
    """Get quiz questions for a chapter"""
    if not SubjectConfig.is_valid_subject(subject):
        raise HTTPException(status_code=400, detail=f"Invalid subject: {subject}")

    try:
        from .rag_service import db

        if db is None:
            raise HTTPException(status_code=500, detail="Database not available")

        quiz_collection = db.quiz_questions
        quiz = quiz_collection.find_one(
            {"subject": subject, "chapter_id": chapter_id},
            {"_id": 0}
        )

        if not quiz:
            return {"questions": [], "message": "No quiz available. Generate one first."}

        return {
            "chapter_id": quiz.get("chapter_id"),
            "chapter_title": quiz.get("chapter_title"),
            "questions": quiz.get("questions", []),
            "generated_at": str(quiz.get("generated_at", ""))
        }

    except Exception as e:
        logger.error(f"Error getting quiz: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))