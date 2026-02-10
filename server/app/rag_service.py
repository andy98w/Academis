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
        logger.info("MongoDB client configured - will connect when first accessed")
    except Exception as e:
        logger.warning(f"Failed to connect to MongoDB: {e}")
        client = None
        db = None
else:
    logger.warning("MONGODB_URI not set - using fallback textbook mode")
    client = None
    db = None

# Subject to collection mapping
SUBJECT_COLLECTIONS = {
    "micro": "economics",
    "macro": "economics",
    "biology": "biology",
    "physics": "physics",
    "chemistry": "chemistry",
}

# Subject display names for prompts
SUBJECT_NAMES = {
    "micro": "AP Microeconomics",
    "macro": "AP Macroeconomics",
    "biology": "AP Biology",
    "physics": "AP Physics",
    "chemistry": "AP Chemistry",
}

def get_collection_for_subject(subject: str) -> str:
    """Get the MongoDB collection name for a subject"""
    if subject not in SUBJECT_COLLECTIONS:
        raise ValueError(f"Unknown subject '{subject}'. Valid subjects: {list(SUBJECT_COLLECTIONS.keys())}")
    return SUBJECT_COLLECTIONS[subject]

def get_subject_name(subject: str) -> str:
    """Get the display name for a subject"""
    return SUBJECT_NAMES.get(subject, "AP Studies")

# Vector stores per collection (lazy loaded)
vector_stores: Dict[str, MongoDBAtlasVectorSearch] = {}

conversation_history: Dict[str, List[Dict[str, str]]] = {}

async def get_fallback_response(question: str, subject: str) -> str:
    """Provide a fallback response when vector store is not available"""
    logger.info("Using fallback response mode")

    model = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.2)
    subject_name = get_subject_name(subject)

    prompt = ChatPromptTemplate.from_template(f"""
    You are an {subject_name} expert. Answer the following question with clear, concise information
    suitable for AP students. Focus on core concepts, definitions, and examples.

    Question: {{question}}

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

async def initialize_vector_store(subject: str):
    """Initialize vector store for a specific subject"""
    global vector_stores

    collection_name = get_collection_for_subject(subject)

    if collection_name in vector_stores:
        return  # Already initialized

    logger.info(f"Initializing vector store for {subject} (collection: {collection_name})...")
    try:
        if db is None:
            logger.warning("MongoDB not available - vector store initialization skipped")
            return

        count = db[collection_name].count_documents({})
        logger.info(f"Found {count} documents in MongoDB collection {collection_name}")

        if count == 0:
            logger.warning(f"No documents found in MongoDB collection {collection_name}")
            return

        embeddings = OpenAIEmbeddings()
        await load_documents(embeddings, subject)
    except Exception as e:
        logger.error(f"Error initializing vector store: {str(e)}")
        logger.error(traceback.format_exc())

async def load_documents(embeddings, subject: str):
    """Load documents for a specific subject"""
    global vector_stores

    collection_name = get_collection_for_subject(subject)

    try:
        collection = db[collection_name]

        count = collection.count_documents({})
        logger.info(f"Found {count} documents in the collection")

        if count == 0:
            raise ValueError(f"No documents found in MongoDB collection {collection_name}")

        indexes = collection.list_indexes()
        vector_index_exists = False
        for index in indexes:
            if "vector_index" in index.get("name", ""):
                vector_index_exists = True
                logger.info("Vector index found in MongoDB collection")
                break

        if not vector_index_exists:
            logger.warning("Vector index not found - Atlas Search index may need to be created")

        vector_stores[collection_name] = MongoDBAtlasVectorSearch(
            collection_name=collection_name,
            embedding=embeddings,
            collection=collection,
            index_name="vector_index",
            text_key="text"
        )

        # Test with a generic query
        _ = vector_stores[collection_name].similarity_search("concept", k=1)

        logger.info(f"Vector store for {subject} initialized and tested successfully")

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


async def get_rag_response(question: str, session_id: str, use_history: bool, subject: str) -> str:
    global vector_stores

    logger.info(f"Processing question for session {session_id} (subject: {subject}): {question[:50]}...")

    collection_name = get_collection_for_subject(subject)

    if collection_name not in vector_stores:
        logger.info(f"Vector store for {subject} not initialized, initializing now")
        await initialize_vector_store(subject)

    if collection_name not in vector_stores:
        logger.warning("Vector store not available - using fallback response")
        return await get_fallback_response(question, subject)

    vector_store = vector_stores[collection_name]

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
        
        # Build search query with subject context
        subject_name = get_subject_name(subject)
        search_query = f"{subject_name} {question}"

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

        tutor_role = f"{subject_name} tutor"
        
        template = f"""You are a {tutor_role}. Use the following reference information and conversation history to answer the student's question.
        If you don't know the answer based on the references, say so and provide general guidance about the topic if possible.

        CRITICAL FORMATTING REQUIREMENTS:
        - NEVER include headings like "From AP Textbooks:" or source attributions
        - NEVER mention where your information comes from
        - Do not use titles, section headings, or source attributions in your answer
        - Present information directly without labeling its origin

        IMPORTANT INSTRUCTIONS FOR FOLLOW-UP QUESTIONS:
        - When the student asks a vague follow-up question like "explain it more," "give me examples," "tell me more," etc., ALWAYS assume "it" refers to the MOST RECENT topic discussed immediately before this question
        - DO NOT mention multiple previous topics or ask for clarification about which topic they mean
        - The most recent exchange in the conversation history is the most relevant context for follow-up questions

        GRAPH/DIAGRAM VISUALIZATION INSTRUCTIONS:
        - When you mention that something is a "graphical representation," "shown on a graph/diagram," "can be visualized," or use similar language, add [GRAPH] at the end of your response
        - Only add [GRAPH] when you specifically mention graphs, charts, curves, diagrams, or visual representations in your explanation
        - Do NOT add [GRAPH] for purely text-based explanations

        {{history_text}}
        References:
        {{context}}

        Student's Question:
        {{question}}

        Answer (remember, NO source attribution or headings, suggest graphs/diagrams when helpful):
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