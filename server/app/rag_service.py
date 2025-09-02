import os
from typing import Optional, List, Dict, Any
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain.schema.output_parser import StrOutputParser
from langchain.prompts import ChatPromptTemplate
from langchain_mongodb import MongoDBAtlasVectorSearch
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import logging
import traceback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv(override=True)

MONGODB_URI = os.getenv("MONGODB_URI")
if MONGODB_URI:
    try:
        client = MongoClient(MONGODB_URI, server_api=ServerApi("1"), connectTimeoutMS=5000, socketTimeoutMS=10000)
        db = client.Academis
        COLLECTION_NAME = "economics"
        logger.info("MongoDB client configured - will connect when first accessed")
    except Exception as e:
        logger.warning(f"Failed to connect to MongoDB: {e}")
        client = None
        db = None
        COLLECTION_NAME = "economics"
else:
    logger.warning("MONGODB_URI not set - using fallback textbook mode")
    client = None
    db = None
    COLLECTION_NAME = "economics"

vector_store: Optional[MongoDBAtlasVectorSearch] = None

conversation_history: Dict[str, List[Dict[str, str]]] = {}

async def get_fallback_response(question: str) -> str:
    """Provide a fallback response when vector store is not available"""
    logger.info("Using fallback response mode")
    
    model = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.2)
    
    prompt = ChatPromptTemplate.from_template("""
    You are an AP Economics expert. Answer the following question with clear, concise information 
    suitable for AP Economics students. Focus on core concepts, definitions, and examples.
    
    Question: {question}
    
    Provide a comprehensive but concise answer covering the key concepts.
    """)
    
    chain = prompt | model | StrOutputParser()
    
    try:
        response = await chain.ainvoke({"question": question})
        logger.info("Fallback response generated successfully")
        return response
    except Exception as e:
        logger.error(f"Error generating fallback response: {str(e)}")
        return "I apologize, but I'm currently unable to process your question. Please check that your OpenAI API key is configured correctly and try again."

async def initialize_vector_store():
    global vector_store
    
    if vector_store is None:
        logger.info("Initializing vector store...")
        try:
            if db is None:
                logger.warning("MongoDB not available - vector store initialization skipped")
                return
                
            count = db[COLLECTION_NAME].count_documents({})
            logger.info(f"Found {count} documents in MongoDB collection {COLLECTION_NAME}")
            
            if count == 0:
                logger.warning(f"No documents found in MongoDB collection {COLLECTION_NAME}")
                return
            
            embeddings = OpenAIEmbeddings()
            await load_documents(embeddings)
        except Exception as e:
            logger.error(f"Error initializing vector store: {str(e)}")
            logger.error(traceback.format_exc())

async def load_documents(embeddings):
    global vector_store
    
    try:
        collection = db[COLLECTION_NAME]
        
        count = collection.count_documents({})
        logger.info(f"Found {count} documents in the collection")

        if count == 0:
            raise ValueError(f"No documents found in MongoDB collection {COLLECTION_NAME}")
        
        indexes = collection.list_indexes()
        vector_index_exists = False
        for index in indexes:
            if "vector_index" in index.get("name", ""):
                vector_index_exists = True
                logger.info("Vector index found in MongoDB collection")
                break
                
        if not vector_index_exists:
            logger.warning("Vector index not found - Atlas Search index may need to be created")
        
        vector_store = MongoDBAtlasVectorSearch(
            collection_name=COLLECTION_NAME,
            embedding=embeddings,
            collection=collection,
            index_name="vector_index",
            text_key="text"
        )
        
        _ = vector_store.similarity_search("economics test", k=1)
        
        logger.info("Vector store initialized and tested successfully")

    except Exception as e:
        logger.error(f"Error initializing vector store: {e}")
        logger.error(traceback.format_exc())
        raise

def get_conversation_history(session_id: str, max_turns: int = 10) -> List[Dict[str, str]]:
    """Get the full conversation history for a specific session"""
    if session_id not in conversation_history:
        conversation_history[session_id] = []

    return conversation_history[session_id]

def add_to_conversation_history(session_id: str, role: str, content: str):
    """Add a message to the conversation history"""
    if session_id not in conversation_history:
        conversation_history[session_id] = []
    
    conversation_history[session_id].append({"role": role, "content": content})
    
    if len(conversation_history[session_id]) > 20:
        conversation_history[session_id] = conversation_history[session_id][-20:]

def detect_economics_topic(question: str) -> str:
    """Detect if a question is more relevant to microeconomics or macroeconomics"""
    micro_keywords = [
        "firm", "consumer", "market structure", "elasticity", "monopoly", 
        "oligopoly", "perfect competition", "price discrimination", "marginal cost",
        "supply and demand", "marginal revenue", "utility", "production", "costs",
        "profit maximization", "consumer surplus", "producer surplus", "efficiency",
        "market failure", "externality", "public good", "microeconomics", "micro-economics"
    ]
    
    macro_keywords = [
        "gdp", "inflation", "unemployment", "monetary policy", "fiscal policy",
        "business cycle", "recession", "economic growth", "aggregate demand",
        "aggregate supply", "money supply", "interest rate", "exchange rate",
        "trade deficit", "national income", "phillips curve", "macroeconomics",
        "macro-economics", "fed", "federal reserve", "central bank", "government spending"
    ]
    
    question_lower = question.lower()
    
    micro_count = sum(1 for keyword in micro_keywords if keyword in question_lower)
    macro_count = sum(1 for keyword in macro_keywords if keyword in question_lower)
    
    if micro_count > macro_count:
        return "micro"
    elif macro_count > micro_count:
        return "macro"
    else:
        return "general"

async def get_rag_response(question: str, session_id: str = "default", use_history: bool = True) -> str:
    global vector_store
    
    logger.info(f"Processing question for session {session_id}: {question[:50]}...")
    
    if vector_store is None:
        logger.info("Vector store not initialized, initializing now")
        await initialize_vector_store()

    if vector_store is None:
        logger.warning("Vector store not available - using fallback response")
        return await get_fallback_response(question)

    try:
        model = ChatOpenAI(model_name="gpt-4o", temperature=0.2)
        
        add_to_conversation_history(session_id, "user", question)
        
        history = get_conversation_history(session_id) if use_history else []
        
        history_text = ""
        if history:
            most_recent_turns = []
            older_history = []

            if len(history) >= 3:
                user_messages = [msg for msg in history[:-1] if msg["role"] == "user"]
                if len(user_messages) >= 2:
                    for i, msg in enumerate(history[:-1]):
                        if msg["role"] == "user" and msg == user_messages[-1]:
                            most_recent_turns.append(msg)
                            if i+1 < len(history)-1 and history[i+1]["role"] == "assistant":
                                most_recent_turns.append(history[i+1])
                            break
                    
                    for msg in history[:-1]:
                        if msg not in most_recent_turns:
                            older_history.append(msg)
            else:
                older_history = history[:-1]
            
            if older_history:
                history_text += "Previous conversation:\n"
                for msg in older_history:
                    prefix = "Student" if msg["role"] == "user" else "Tutor"
                    history_text += f"{prefix}: {msg['content']}\n"
                history_text += "\n"
            
            if most_recent_turns:
                history_text += "MOST RECENT EXCHANGE (PRIMARY CONTEXT FOR FOLLOW-UP QUESTIONS):\n"
                for msg in most_recent_turns:
                    prefix = "Student" if msg["role"] == "user" else "Tutor"
                    history_text += f"{prefix}: {msg['content']}\n"
                history_text += "\n"
        
        econ_topic = detect_economics_topic(question)
        logger.info(f"Detected economics topic: {econ_topic}")
        
        search_query = question
        if "micro" in session_id or econ_topic == "micro":
            search_query = f"microeconomics {question}"
        elif "macro" in session_id or econ_topic == "macro":
            search_query = f"macroeconomics {question}"
        
        docs = vector_store.similarity_search(search_query, k=4)
        logger.info(f"Retrieved {len(docs)} relevant documents")
        
        context_texts = []
        for doc in docs:
            if hasattr(doc, 'page_content') and doc.page_content:
                context_texts.append(doc.page_content)
            elif hasattr(doc, 'text') and doc.text:
                context_texts.append(doc.text)
            elif isinstance(doc, dict) and doc.get('text'):
                context_texts.append(doc['text'])
        
        context = "\n\n".join(context_texts)
        
        tutor_role = "AP Economics tutor"
        if "micro" in session_id or econ_topic == "micro":
            tutor_role = "AP Microeconomics tutor" 
        elif "macro" in session_id or econ_topic == "macro":
            tutor_role = "AP Macroeconomics tutor"
        
        template = f"""You are an {tutor_role}. Use the following reference information and conversation history to answer the student's question.
        If you don't know the answer based on the references, say so and provide general guidance about the topic if possible.
        
        CRITICAL FORMATTING REQUIREMENTS:
        - NEVER include headings like "Supply and Demand Examples:" or "From AP Economics Textbooks:"
        - NEVER mention where your information comes from
        - Do not use titles, section headings, or source attributions in your answer
        - Present information directly without labeling its origin
        
        IMPORTANT INSTRUCTIONS FOR FOLLOW-UP QUESTIONS:
        - When the student asks a vague follow-up question like "explain it more," "give me examples," "tell me more," etc., ALWAYS assume "it" refers to the MOST RECENT topic discussed immediately before this question
        - DO NOT mention multiple previous topics or ask for clarification about which topic they mean
        - The most recent exchange in the conversation history is the most relevant context for follow-up questions
        - For example, if the last topic was "supply and demand" and the student asks "explain it with examples," give examples of supply and demand, not any earlier topics
        
        GRAPH VISUALIZATION INSTRUCTIONS:
        - When you mention that something is a "graphical representation," "shown on a graph," "can be visualized," or use similar language, add [GRAPH] at the end of your response
        - Only add [GRAPH] when you specifically mention graphs, charts, curves, or visual representations in your explanation
        - Do NOT add [GRAPH] for purely text-based explanations
        - Examples:
          * "The PPF is a graphical representation of..." → add [GRAPH]
          * "Supply and demand curves show..." → add [GRAPH] 
          * "This can be illustrated on a graph..." → add [GRAPH]
          * "Scarcity means limited resources" → do NOT add [GRAPH]
        
        {{history_text}}
        References:
        {{context}}
        
        Student's Question:
        {{question}}
        
        Answer (remember, NO source attribution or headings, suggest graphs when helpful):
        """
        
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | model | StrOutputParser()
        response = await chain.ainvoke({
            "context": context, 
            "question": question,
            "history_text": history_text
        })
        
        # Check for graph suggestion and generate if needed
        try:
            from .graph_response_handler import graph_response_handler
            
            cleaned_response, should_generate_graph, graph_desc = graph_response_handler.extract_graph_suggestion(response)
            
            result = {"text": cleaned_response}
            
            if should_generate_graph:
                try:
                    graph_data = await graph_response_handler.generate_contextual_graph(cleaned_response, question)
                    if graph_data:
                        result["graph"] = graph_data
                        logger.info(f"Generated {graph_data['type']} graph for response")
                except Exception as e:
                    logger.error(f"Error generating graph for response: {e}")
        except ImportError as e:
            logger.warning(f"Graph functionality disabled due to missing dependencies: {e}")
            cleaned_response = response.replace('[GRAPH]', '').strip() if '[GRAPH]' in response else response
            result = {"text": cleaned_response}
        
        add_to_conversation_history(session_id, "assistant", cleaned_response)
        logger.info(f"Generated response of length {len(cleaned_response)}")
        
        return result
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        error_message = f"I'm sorry, I encountered an error while trying to answer your question: {str(e)}"
        add_to_conversation_history(session_id, "assistant", error_message)
        return error_message