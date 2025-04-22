from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from .rag_service import get_rag_response
from .textbook_service import get_textbook_content, get_textbook_toc
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8080, reload=True)