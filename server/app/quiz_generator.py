"""
Quiz Generator Service

Generates AP-style multiple-choice questions for textbook chapters.
Questions can include text, tables, or graphs for visual questions.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv(override=True)
logger = logging.getLogger(__name__)

# Tool definitions for quiz generation
QUIZ_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_table_question",
            "description": "Create a question that includes a data table. Use for questions about data interpretation, comparisons, or calculations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The question text that references the table"
                    },
                    "table_title": {
                        "type": "string",
                        "description": "Title for the table"
                    },
                    "columns": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Column headers for the table"
                    },
                    "rows": {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "description": "Row data for the table"
                    },
                    "options": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Four answer options (A, B, C, D)"
                    },
                    "correct": {
                        "type": "integer",
                        "description": "Index of correct answer (0-3)"
                    },
                    "explanation": {
                        "type": "string",
                        "description": "Explanation of why the answer is correct"
                    }
                },
                "required": ["question", "table_title", "columns", "rows", "options", "correct", "explanation"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_graph_question",
            "description": "Create a question that requires a graph/chart visualization. Use for supply/demand curves, cost curves, or other economic graphs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The question text that references the graph"
                    },
                    "graph_spec": {
                        "type": "object",
                        "properties": {
                            "chart_type": {"type": "string", "description": "Type: line_chart, supply_demand, cost_curves, etc."},
                            "title": {"type": "string"},
                            "description": {"type": "string", "description": "Detailed description of what the graph shows"},
                            "x_axis": {"type": "string"},
                            "y_axis": {"type": "string"},
                            "curves": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "points": {
                                            "type": "array",
                                            "items": {
                                                "type": "array",
                                                "items": {"type": "number"}
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "description": "Specification for generating the graph"
                    },
                    "options": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Four answer options (A, B, C, D)"
                    },
                    "correct": {
                        "type": "integer",
                        "description": "Index of correct answer (0-3)"
                    },
                    "explanation": {
                        "type": "string",
                        "description": "Explanation of why the answer is correct"
                    }
                },
                "required": ["question", "graph_spec", "options", "correct", "explanation"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_text_question",
            "description": "Create a standard text-only multiple choice question.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The question text"
                    },
                    "options": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Four answer options (A, B, C, D)"
                    },
                    "correct": {
                        "type": "integer",
                        "description": "Index of correct answer (0-3)"
                    },
                    "explanation": {
                        "type": "string",
                        "description": "Explanation of why the answer is correct"
                    }
                },
                "required": ["question", "options", "correct", "explanation"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "finish_quiz",
            "description": "Call this when you have generated all questions to finalize the quiz.",
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {
                        "type": "string",
                        "description": "Brief summary of the quiz coverage"
                    }
                },
                "required": ["summary"]
            }
        }
    }
]

SYSTEM_PROMPT = """You are an AP exam question writer. Generate high-quality multiple-choice questions for AP {subject} based on the chapter content provided.

Requirements:
1. Create exactly {num_questions} questions
2. Questions should test understanding, not just memorization
3. Include a mix of:
   - Conceptual questions (text only)
   - Data interpretation questions (with tables)
   - Graph analysis questions (with graphs) - especially for economics concepts like supply/demand curves
4. All options should be plausible (good distractors)
5. Explanations should clearly explain why the correct answer is right AND why others are wrong
6. Match AP exam difficulty level

For each question, call the appropriate tool:
- create_text_question: For conceptual questions
- create_table_question: For data/calculation questions
- create_graph_question: For visual/curve analysis questions

When done, call finish_quiz to complete.

Chapter Content:
{content}

Key Topics to Cover:
{topics}
"""


class QuizGenerator:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o")

    async def generate_quiz(
        self,
        subject: str,
        chapter_content: List[str],
        topics: List[str],
        num_questions: int = 5
    ) -> List[Dict[str, Any]]:
        """Generate quiz questions for a chapter."""

        questions = []
        content_text = "\n\n".join(chapter_content[:15])  # Use first 15 paragraphs
        topics_text = "\n".join(f"- {t}" for t in topics) if topics else "- Key concepts from this chapter"

        system_prompt = SYSTEM_PROMPT.format(
            subject=subject,
            num_questions=num_questions,
            content=content_text,
            topics=topics_text
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Generate {num_questions} AP-style multiple choice questions. Include at least 1 question with a table or graph if the content involves data or curves."}
        ]

        max_iterations = 15
        finished = False

        for iteration in range(max_iterations):
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=QUIZ_TOOLS,
                    tool_choice="auto",
                    temperature=0.7
                )

                message = response.choices[0].message

                if not message.tool_calls:
                    logger.info("[Quiz] No more tool calls, finishing")
                    break

                # Process tool calls
                tool_results = []
                for tool_call in message.tool_calls:
                    fn_name = tool_call.function.name
                    try:
                        args = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        args = {}

                    logger.info(f"[Quiz] Tool call: {fn_name}")

                    if fn_name == "create_text_question":
                        question = {
                            "type": "text",
                            "question": args.get("question", ""),
                            "options": args.get("options", []),
                            "correct": args.get("correct", 0),
                            "explanation": args.get("explanation", "")
                        }
                        questions.append(question)
                        result = f"Created text question #{len(questions)}"

                    elif fn_name == "create_table_question":
                        question = {
                            "type": "table",
                            "question": args.get("question", ""),
                            "table": {
                                "title": args.get("table_title", ""),
                                "columns": args.get("columns", []),
                                "rows": args.get("rows", [])
                            },
                            "options": args.get("options", []),
                            "correct": args.get("correct", 0),
                            "explanation": args.get("explanation", "")
                        }
                        questions.append(question)
                        result = f"Created table question #{len(questions)}"

                    elif fn_name == "create_graph_question":
                        # Generate the actual graph image
                        graph_spec = args.get("graph_spec", {})
                        graph_image = await self._generate_graph_image(graph_spec)

                        question = {
                            "type": "graph",
                            "question": args.get("question", ""),
                            "graph": {
                                "spec": graph_spec,
                                "image": graph_image  # Base64 image
                            },
                            "options": args.get("options", []),
                            "correct": args.get("correct", 0),
                            "explanation": args.get("explanation", "")
                        }
                        questions.append(question)
                        result = f"Created graph question #{len(questions)}"

                    elif fn_name == "finish_quiz":
                        finished = True
                        result = f"Quiz complete with {len(questions)} questions"

                    else:
                        result = f"Unknown tool: {fn_name}"

                    tool_results.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "content": result
                    })

                # Add assistant message and tool results
                messages.append({"role": "assistant", "content": message.content, "tool_calls": message.tool_calls})
                messages.extend(tool_results)

                if finished or len(questions) >= num_questions:
                    break

            except Exception as e:
                logger.error(f"[Quiz] Error in iteration {iteration}: {e}")
                break

        logger.info(f"[Quiz] Generated {len(questions)} questions")
        return questions

    async def _generate_graph_image(self, graph_spec: Dict[str, Any]) -> Optional[str]:
        """Generate a graph image from spec using the graph service."""
        try:
            from .graph_service import GraphGenerationService

            graph_service = GraphGenerationService()
            description = graph_spec.get("description", "")
            title = graph_spec.get("title", "Graph")

            # Generate graph
            result = await graph_service.generate_graph(
                context=description,
                title=title
            )

            if result and "image" in result:
                return result["image"]

            return None
        except Exception as e:
            logger.error(f"[Quiz] Graph generation error: {e}")
            return None


# Singleton instance
quiz_generator = QuizGenerator()
