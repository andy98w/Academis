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
            "description": "Create a question that requires a graph/chart visualization. Use for any visual concepts: curves, graphs, diagrams. IMPORTANT: If your question references specific points (A, B, C, D, etc.), you MUST include them in labeled_points.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The question text that references the graph. If referencing labeled points, they MUST be defined in labeled_points."
                    },
                    "graph_spec": {
                        "type": "object",
                        "properties": {
                            "chart_type": {"type": "string", "description": "Type: line_chart, curve, scatter, bar_chart"},
                            "title": {"type": "string"},
                            "description": {"type": "string", "description": "Detailed description of what the graph shows"},
                            "x_axis": {"type": "string", "description": "X-axis label"},
                            "y_axis": {"type": "string", "description": "Y-axis label"},
                            "curves": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string", "description": "Curve name (e.g., 'Growth Rate', 'Concentration', 'Velocity')"},
                                        "shape": {"type": "string", "description": "Shape: linear, concave, convex, u_shape, exponential, logarithmic"},
                                        "direction": {"type": "string", "description": "Direction: increasing, decreasing"}
                                    }
                                }
                            },
                            "labeled_points": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "label": {"type": "string", "description": "Point label (A, B, C, D, etc.)"},
                                        "x": {"type": "number", "description": "X position along curve (0-100), e.g., 20=left, 50=middle, 80=right"},
                                        "description": {"type": "string", "description": "CRITICAL: This determines Y placement. Use: 'on the curve', 'below curve' (inefficient region), 'above curve', 'at intersection/equilibrium'"}
                                    },
                                    "required": ["label", "x", "description"]
                                },
                                "description": "REQUIRED if question references points. The description field determines exact Y placement on/off the curve."
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

CHAPTER TITLE: {chapter_title}

Requirements:
1. Create exactly {num_questions} questions
2. Questions should test understanding, not just memorization
3. Include a mix of:
   - Conceptual questions (text only)
   - Data interpretation questions (with tables)
   - Graph analysis questions (with graphs) - when the content involves visual concepts, curves, or data relationships
4. All options should be plausible (good distractors)
5. Match AP exam difficulty level

CRITICAL - FOCUS ON THIS CHAPTER'S UNIQUE CONTENT:
- Only ask about concepts that are SPECIFIC to this chapter
- Do NOT ask generic questions about concepts that appear in multiple chapters
- Read the chapter title and content carefully to identify what makes THIS chapter unique
- Test on the specific formulas, methods, and examples taught in THIS chapter

CRITICAL - EXPLANATION REQUIREMENTS:
Every explanation MUST be DETAILED and include:
- WHY the correct answer is right
- Step-by-step MATH/CALCULATIONS for any numerical questions
- Brief mention of why at least one wrong answer is incorrect

Example explanation for a table/calculation question:
"From the table: Value X = 200 and Value Y = 100.
Using the formula: Result = X ÷ Y = 200 ÷ 100 = 2.
The correct answer is 2.
Option A (0.5) incorrectly inverted the calculation."

For each question, call the appropriate tool:
- create_text_question: For conceptual questions
- create_table_question: For data/calculation questions - explanation MUST show calculation steps using table data
- create_graph_question: For visual/curve analysis questions

CRITICAL FOR TABLE QUESTIONS:
- Your explanation MUST reference specific numbers from the table
- Show the formula being used
- Substitute actual values and calculate step-by-step

CRITICAL FOR GRAPH QUESTIONS:
- If your question asks about specific points (A, B, C, D), you MUST define them in labeled_points
- Each labeled_point needs: label, x position (0-100), and description
- Description determines placement: "on the curve", "below curve" (inside region), "above curve" (outside region)

When done, call finish_quiz to complete.

Chapter Content:
{content}

Based on the chapter content above, identify the KEY CONCEPTS unique to this chapter and generate questions that test understanding of those specific concepts.
"""


class QuizGenerator:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o")

    async def generate_quiz(
        self,
        subject: str,
        chapter_content: List[str],
        chapter_title: str = "",
        num_questions: int = 5
    ) -> List[Dict[str, Any]]:
        """Generate quiz questions for a chapter."""

        questions = []
        content_text = "\n\n".join(chapter_content[:15])  # Use first 15 paragraphs

        system_prompt = SYSTEM_PROMPT.format(
            subject=subject,
            chapter_title=chapter_title or "Unknown Chapter",
            num_questions=num_questions,
            content=content_text
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
        """Generate a graph image from spec, rendering labeled points directly."""
        try:
            import matplotlib.pyplot as plt
            import numpy as np
            import io
            import base64

            # Create figure
            fig, ax = plt.subplots(figsize=(8, 6))

            title = graph_spec.get("title", "Graph")
            x_label = graph_spec.get("x_axis", "Quantity")
            y_label = graph_spec.get("y_axis", "Price")
            curves = graph_spec.get("curves", [])
            labeled_points = graph_spec.get("labeled_points", [])

            # Set up axes
            ax.set_xlim(0, 100)
            ax.set_ylim(0, 100)
            ax.set_xlabel(x_label, fontsize=11)
            ax.set_ylabel(y_label, fontsize=11)
            ax.set_title(title, fontsize=13, fontweight='bold')

            # Color palette for curves
            colors = ['#2563eb', '#dc2626', '#16a34a', '#9333ea']

            # Determine primary curve type from title/curves for point placement
            title_lower = title.lower()
            description_lower = graph_spec.get("description", "").lower()

            # Detect curve characteristics from title and description
            is_boundary_curve = any(term in title_lower or term in description_lower for term in [
                "ppc", "possibilit", "frontier", "boundary", "constraint", "limit"
            ])
            is_equilibrium_graph = any(term in title_lower or term in description_lower for term in [
                "supply", "demand", "equilibrium", "market", "intersection"
            ])

            # Define curve function for point placement
            def get_curve_y(x_val, curve_type):
                if curve_type == "concave":
                    return 90 * np.sqrt(np.maximum(0, 1 - (x_val/100)**2))
                elif curve_type == "convex":
                    return 100 - 90 * np.sqrt(np.maximum(0, 1 - (x_val/100)**2))
                elif curve_type == "u_shape":
                    return 20 + 0.015 * (x_val - 50)**2
                elif curve_type == "decreasing":
                    return 90 - 0.8 * x_val
                else:  # increasing
                    return 10 + 0.8 * x_val

            # Draw curves
            x = np.linspace(0, 100, 100)
            primary_curve_type = None

            for i, curve in enumerate(curves):
                color = colors[i % len(colors)]
                name = curve.get("name", f"Curve {i+1}")
                shape = curve.get("shape", "linear")
                direction = curve.get("direction", "increasing")

                # Determine curve type from shape/direction
                if shape == "concave" or (is_boundary_curve and shape != "linear"):
                    curve_type = "concave"
                elif shape == "convex":
                    curve_type = "convex"
                elif shape == "u_shape":
                    curve_type = "u_shape"
                elif shape == "exponential":
                    curve_type = "increasing"  # Exponential uses increasing for now
                elif shape == "logarithmic":
                    curve_type = "concave"  # Logarithmic similar to concave shape
                elif direction == "decreasing":
                    curve_type = "decreasing"
                else:
                    curve_type = "increasing"

                if primary_curve_type is None:
                    primary_curve_type = curve_type

                y = get_curve_y(x, curve_type)
                ax.plot(x, y, color=color, linewidth=2.5, label=name)

            # Default curve type if no curves defined
            if primary_curve_type is None:
                if is_boundary_curve:
                    primary_curve_type = "concave"
                elif is_equilibrium_graph:
                    primary_curve_type = "decreasing"
                else:
                    primary_curve_type = "decreasing"  # General default

            # Draw labeled points - CALCULATE ACTUAL POSITIONS BASED ON CURVE
            point_colors = {'A': '#2563eb', 'B': '#dc2626', 'C': '#16a34a', 'D': '#9333ea', 'E': '#f59e0b'}

            for point in labeled_points:
                label = point.get("label", "?")
                px = point.get("x", 50)
                desc = point.get("description", "").lower()
                color = point_colors.get(label, '#000000')

                # Calculate actual y position based on description and curve
                curve_y = get_curve_y(px, primary_curve_type)

                # Determine Y position based on semantic description
                if "on" in desc and ("curve" in desc or "line" in desc or "frontier" in desc or "boundary" in desc):
                    # Place exactly on the curve
                    py = curve_y
                elif any(term in desc for term in ["inside", "below", "inefficient", "under", "beneath"]):
                    # Place below the curve
                    py = curve_y * 0.45
                elif any(term in desc for term in ["outside", "above", "unattainable", "beyond", "over"]):
                    # Place above the curve
                    py = min(95, curve_y * 1.3 + 10)
                elif any(term in desc for term in ["equilibrium", "intersection", "optimal", "maximum", "minimum"]):
                    # Place at special point (middle or curve value)
                    py = curve_y if "on" in desc else 50
                else:
                    # Fallback: use curve Y or provided y
                    py = point.get("y", curve_y)

                # Draw the point
                ax.scatter([px], [py], s=150, color=color, zorder=5, edgecolors='white', linewidths=2)
                # Add label with offset
                ax.annotate(label, (px, py), xytext=(10, 10), textcoords='offset points',
                           fontsize=16, fontweight='bold', color=color,
                           bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))

            if curves:
                ax.legend(loc='upper right', fontsize=10)

            ax.grid(True, alpha=0.3)
            fig.tight_layout()

            # Convert to base64
            buffer = io.BytesIO()
            fig.savefig(buffer, format='png', dpi=150, bbox_inches='tight',
                       facecolor='white', edgecolor='none')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
            plt.close(fig)

            return image_base64

        except Exception as e:
            logger.error(f"[Quiz] Graph generation error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None


# Singleton instance
quiz_generator = QuizGenerator()
