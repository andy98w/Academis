import os
import asyncio
import logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.tools import Tool
from .rag_service import get_rag_response, detect_economics_topic

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

conversation_memory = {}

class EconomicsAgent:
    """Agent that combines RAG with web search and YouTube for comprehensive AP Economics answers"""
    
    def __init__(self):
        self.model = ChatOpenAI(temperature=0, model="gpt-4o", max_tokens=1024)
        self.tools = self._initialize_tools()
        
    def _initialize_tools(self) -> List[Tool]:
        """Initialize the tools available to the agent"""
        tools = []
        
        tools.append(
            Tool(
                name="AP_Economics_Textbooks",
                func=self._search_vector_db_async,
                description="Search AP Economics textbooks to find authoritative information about economics concepts, theories, and principles. Use this tool for foundational economics knowledge and AP exam topics."
            )
        )
        

        
        return tools
    
    async def _search_vector_db_async(self, query: str, original_session_id: str = None) -> str:
        """Direct access to RAG for textbook content"""
        econ_topic = detect_economics_topic(query)
        topic_prefix = ""
        if econ_topic == "micro":
            topic_prefix = "[Microeconomics] "
        elif econ_topic == "macro":
            topic_prefix = "[Macroeconomics] "
            
        enhanced_query = f"{topic_prefix}{query}"
        if original_session_id:
            session_id = f"{original_session_id}_rag"
        else:
            session_id = f"agent_{econ_topic}" if econ_topic != "general" else "agent"
        
        try:
            logger.info(f"Directly querying RAG with: {enhanced_query[:50]}...")
            result = await get_rag_response(
                question=enhanced_query, 
                session_id=session_id,
                use_history=True
            )
            
            if result and len(result) > 20:
                logger.info(f"RAG returned {len(result)} char response")
                return result
            else:
                logger.warning("RAG returned empty or very short response")
                return "I don't have enough information to answer this question. Could you please rephrase or ask a different economics question?"
        except Exception as e:
            logger.error(f"Error in RAG search: {e}")
            return "I'm sorry, I encountered an error while searching for information. Please try again."
    
    def create_agent(self) -> AgentExecutor:
        """Create an agent with the defined tools"""
        prompt = ChatPromptTemplate.from_template("""
        You are an AP Economics Expert, providing clear, concise answers.
        
        Use these tools efficiently:
        1. AP_Economics_Textbooks: Check academic references for comprehensive information
        
        CRITICAL FORMATTING REQUIREMENTS:
        - NEVER include headings like "Supply and Demand Examples:" or "From AP Economics Textbooks:"
        - NEVER mention where your information comes from or include source attributions
        - Do not use titles, section headings, or source labels in your answer
        - Present information directly without formatting that reveals its origin
        - Do not say phrases like "According to AP Economics textbooks" or "Based on the information"
        - Never include phrases like "From my knowledge" or "From the search results"
        
        Guidelines:
        - Be concise and efficient with tool usage
        - Limit searches to 1-2 queries
        - Provide brief, focused answers
        - Use bullet points or short paragraphs
        
        IMPORTANT INSTRUCTIONS FOR FOLLOW-UP QUESTIONS:
        - When the student asks a vague follow-up question like "explain it more," "give me examples," "tell me more," etc., ALWAYS assume "it" refers to the MOST RECENT topic discussed immediately before this question
        - DO NOT mention multiple previous topics or ask for clarification about which topic they mean
        - The most recent exchange in the conversation history is the most relevant context for follow-up questions
        - For example, if the last topic was "supply and demand" and the student asks "explain it with examples," give examples of supply and demand, not any earlier topics
        
        {input}
        
        {agent_scratchpad}
        """)

        agent = create_openai_tools_agent(self.model, self.tools, prompt)
        agent_executor = AgentExecutor(
            agent=agent, 
            tools=self.tools, 
            verbose=True,
            max_iterations=3,
            handle_parsing_errors=True
        )
        
        return agent_executor
    
    def _get_conversation_context(self, session_id: str) -> str:
        """Get the full conversation history for a session as formatted context"""
        if session_id not in conversation_memory:
            return ""
            
        history = conversation_memory[session_id]
        if not history:
            return ""

        most_recent_turns = []
        older_history = []
        
        if len(history) >= 2:
            user_messages = [msg for msg in history if msg["is_user"]]
            if len(user_messages) >= 2:
                prev_user_msg = user_messages[-2]
                
                for i, msg in enumerate(history):
                    if msg == prev_user_msg and i+1 < len(history) and not history[i+1]["is_user"]:
                        most_recent_turns.append(msg)
                        most_recent_turns.append(history[i+1])
                        break
                
                for msg in history:
                    if msg not in most_recent_turns:
                        older_history.append(msg)
        else:
            older_history = history
        
        context_parts = []
        
        if older_history:
            context_parts.append("Previous conversation:")
            for msg in older_history:
                prefix = "Student" if msg["is_user"] else "Assistant"
                message_text = msg["text"]
                if len(message_text) > 300:
                    message_text = message_text[:300] + "..."
                context_parts.append(f"{prefix}: {message_text}")
            context_parts.append("")
            
        if most_recent_turns:
            context_parts.append("MOST RECENT EXCHANGE (PRIMARY CONTEXT FOR FOLLOW-UP QUESTIONS):")
            for msg in most_recent_turns:
                prefix = "Student" if msg["is_user"] else "Assistant"
                message_text = msg["text"]
                if len(message_text) > 300:
                    message_text = message_text[:300] + "..."
                context_parts.append(f"{prefix}: {message_text}")
            context_parts.append("")
            
        return "\n".join(context_parts)
    
    def _add_to_memory(self, session_id: str, text: str, is_user: bool):
        """Add a message to the conversation memory"""
        if session_id not in conversation_memory:
            conversation_memory[session_id] = []

        conversation_memory[session_id].append({
            "text": text,
            "is_user": is_user,
            "timestamp": str(asyncio.get_event_loop().time())
        })
        
        if len(conversation_memory[session_id]) > 20:
            conversation_memory[session_id] = conversation_memory[session_id][-20:]
    
    async def get_response(self, question: str, session_id: str = "default") -> str:
        """Get a focused agent response to an economics question with timeout protection"""
        try:
            logger.info(f"Agent processing question: {question[:50]}... [session: {session_id}]")
            
            self._add_to_memory(session_id, question, is_user=True)
            
            agent_executor = self.create_agent()
            
            conversation_context = self._get_conversation_context(session_id)
            
            context = ""
            if "micro" in session_id or "micro" in question.lower():
                context = "This is a microeconomics question. "
            elif "macro" in session_id or "macro" in question.lower():
                context = "This is a macroeconomics question. "
            
            enhanced_question = f"{context}{conversation_context}Current question: {question}"
            
            logger.info("Starting agent execution with timeout")
            
            try:
                timeout_seconds = 25
                logger.info(f"Setting timeout of {timeout_seconds} seconds")
                
                loop = asyncio.get_event_loop()
                result = await asyncio.wait_for(
                    loop.run_in_executor(None, lambda: agent_executor.invoke({"input": enhanced_question})),
                    timeout=timeout_seconds
                )
                answer = result.get("output", "")
            except asyncio.TimeoutError:
                logger.warning("Agent timed out, falling back to RAG-only response")
                answer = await self._search_vector_db_async(question, original_session_id=session_id)
            
            if (not answer.strip() or
                len(answer) < 50 or 
                "Agent stopped due to max iterations" in answer or
                "I couldn't find" in answer):
                
                logger.warning(f"Agent returned problematic answer: '{answer}'. Using RAG fallback")
                
                rag_answer = await self._search_vector_db_async(question, original_session_id=session_id)
                
                if rag_answer and len(rag_answer) > 100:
                    answer = rag_answer
                else:
                    answer = "I don't have enough information to answer that question completely. Could you please ask a different economics question?"
            
            logger.info(f"Response generated: {len(answer)} chars")
            
            self._add_to_memory(session_id, answer, is_user=False)
            
            return answer
            
        except Exception as e:
            logger.error(f"Agent error: {e}")
            try:
                logger.info("Attempting RAG fallback after agent error")
                rag_response = await self._search_vector_db_async(question, original_session_id=session_id)
                if rag_response and len(rag_response) > 20:
                    self._add_to_memory(session_id, rag_response, is_user=False)
                    return rag_response
            except Exception:
                pass
                
            return f"I'm sorry, I couldn't answer your economics question at this time. Please try again with a different question."

economics_agent = EconomicsAgent()