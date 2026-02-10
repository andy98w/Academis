import os
import asyncio
import logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.tools import Tool
from .rag_service import get_rag_response, get_subject_name

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv(override=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

conversation_memory = {}


class SubjectAgent:
    """Generic agent that handles any AP subject with RAG-powered responses"""

    def __init__(self, subject: str):
        self.subject = subject
        self.subject_name = get_subject_name(subject)
        self.model = ChatOpenAI(temperature=0, model="gpt-4o", max_tokens=1024)

    def _is_subject_question(self, question: str) -> bool:
        """Check if a question is likely about the subject (vs casual chat)"""
        question_words = ['what', 'why', 'how', 'explain', 'define', 'describe', 'compare', 'analyze']
        question_lower = question.lower()
        return any(w in question_lower for w in question_words) or len(question.split()) > 5

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

    async def _search_rag(self, query: str, session_id: str) -> str:
        """Search RAG for the current subject"""
        try:
            logger.info(f"Querying RAG for {self.subject}: {query[:50]}...")
            result = await get_rag_response(
                question=query,
                session_id=f"{session_id}_rag",
                use_history=True,
                subject=self.subject
            )

            if result and len(str(result)) > 20:
                # Handle both string and dict responses
                if isinstance(result, dict):
                    return result.get("text", str(result))
                return result
            else:
                logger.warning("RAG returned empty or very short response")
                return ""
        except Exception as e:
            logger.error(f"Error in RAG search: {e}")
            return ""

    async def _get_conversational_response(self, question: str, session_id: str, rag_context: str = "") -> str:
        """Use LLM to generate a natural response, with optional RAG context"""
        from langchain.schema import HumanMessage, SystemMessage

        conversation_history = self._get_conversation_context(session_id)

        system_prompt = f"""You are a friendly and helpful {self.subject_name} tutor. You help students learn and prepare for the AP exam.

Guidelines:
- Be conversational and friendly for greetings, thanks, and casual chat
- For subject questions, provide clear, accurate explanations with examples
- Keep responses concise but informative (2-4 paragraphs for substantive questions)
- Use bullet points or bold text for key concepts when helpful
- If you don't know something, say so honestly

{f"Use this reference material to help answer: {rag_context[:2000]}" if rag_context else ""}"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"{conversation_history}\nStudent: {question}")
        ]

        response = await self.model.ainvoke(messages)
        return response.content

    async def get_response(self, question: str, session_id: str = "default") -> str:
        """Get a conversational response to any message"""
        try:
            logger.info(f"Processing ({self.subject}): {question[:50]}... [session: {session_id}]")

            self._add_to_memory(session_id, question, is_user=True)

            is_subject_question = self._is_subject_question(question)

            rag_context = ""
            if is_subject_question:
                logger.info(f"Fetching RAG context for {self.subject} question")
                rag_context = await self._search_rag(question, session_id)

            # Generate response using LLM
            answer = await self._get_conversational_response(question, session_id, rag_context)

            if not answer or len(answer) < 10:
                answer = f"I'm here to help with {self.subject_name}! Feel free to ask me about any concept."

            logger.info(f"Response generated: {len(answer)} chars")

            self._add_to_memory(session_id, answer, is_user=False)

            return answer

        except Exception as e:
            logger.error(f"Agent error: {e}")
            try:
                logger.info("Attempting RAG fallback after agent error")
                rag_response = await self._search_rag(question, session_id)
                if rag_response and len(rag_response) > 20:
                    self._add_to_memory(session_id, rag_response, is_user=False)
                    return rag_response
            except Exception:
                pass

            return f"I'm sorry, I couldn't answer your question at this time. Please try again."


# Cache of agents per subject
_agents: Dict[str, SubjectAgent] = {}


def get_agent(subject: str) -> SubjectAgent:
    """Get or create an agent for a specific subject"""
    if subject not in _agents:
        _agents[subject] = SubjectAgent(subject)
    return _agents[subject]
