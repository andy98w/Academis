"""
Agentic Textbook Generator

Uses OpenAI's tool-calling API with a custom agent loop to let GPT-4o
autonomously decide when to:
- Search the web for current examples
- Query the textbook RAG for authoritative content
- Generate graphs for visual concepts
- Create tables for comparisons

A custom loop (not LangChain AgentExecutor) ensures the agent actually
calls create_graph / create_table before finishing.
"""

import os
import re
import json
import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple

from openai import AsyncOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from dotenv import load_dotenv

load_dotenv(override=True)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Shared state for tool results (collected during agent execution)
# ---------------------------------------------------------------------------
_generated_assets: Dict[str, Dict[str, Any]] = {}
_asset_counter: int = 0
_current_subject: str = ""


def _reset_assets():
    global _generated_assets, _asset_counter
    _generated_assets = {}
    _asset_counter = 0


def _next_asset_id(prefix: str = "viz") -> str:
    global _asset_counter
    _asset_counter += 1
    return f"{prefix}_{_asset_counter}"


# ---------------------------------------------------------------------------
# Tool implementations (plain functions, no decorators)
# ---------------------------------------------------------------------------

# --- Web Search ---
_tavily_tool: Optional[TavilySearchResults] = None


def _get_tavily():
    global _tavily_tool
    if _tavily_tool is None:
        key = os.getenv("TAVILY_API_KEY")
        if key:
            try:
                _tavily_tool = TavilySearchResults(max_results=3)
            except Exception as e:
                logger.warning(f"Could not initialise Tavily: {e}")
    return _tavily_tool


def tool_search_web(query: str) -> str:
    """Execute a web search via Tavily."""
    tavily = _get_tavily()
    if not tavily:
        return "(Web search unavailable — TAVILY_API_KEY not set)"
    try:
        results = tavily.run(query)
        if isinstance(results, list):
            parts = []
            for r in results[:3]:
                if isinstance(r, dict):
                    c = r.get("content", "")
                    if c:
                        parts.append(c)
            return "\n\n".join(parts) or "(No results found)"
        return str(results) if results else "(No results found)"
    except Exception as e:
        logger.error(f"Web search error: {e}")
        return f"(Search error: {e})"


# --- RAG Textbook Query ---
_rag_initialized = False


async def tool_query_textbook(topic: str) -> str:
    """Retrieve authoritative textbook content from the RAG knowledge base."""
    global _rag_initialized
    try:
        from .rag_service import get_rag_response, initialize_vector_store

        if not _rag_initialized:
            await initialize_vector_store(_current_subject)
            _rag_initialized = True

        session_id = f"agent_rag_{topic.replace(' ', '_')[:40]}"
        rag_query = (
            f"Find authoritative educational content about: {topic}\n"
            "Focus on definitions, key principles, and academic explanations."
        )
        result = await get_rag_response(rag_query, session_id, False, _current_subject)

        if isinstance(result, dict):
            return result.get("text", "(No content found)")
        return str(result) if result else "(No content found)"
    except Exception as e:
        logger.error(f"RAG query error: {e}")
        return f"(Textbook query error: {e})"


# --- Create Graph ---
async def tool_create_graph(title: str, spec: str) -> str:
    """Create a graph by rendering a JSON visualization spec directly.

    The agent provides a full rendering specification (chart_type, series,
    axes, key_points, etc.) so no intermediate LLM interpretation is needed.
    This produces more accurate graphs because the agent controls every detail.
    """
    try:
        from .graph_service import universal_graph_generator

        parsed_spec = json.loads(spec)
        # Ensure title is in the spec
        parsed_spec.setdefault("title", title)

        # Render directly — skip the two LLM calls (analyze + extract)
        image_base64 = await universal_graph_generator._render_graph(parsed_spec)

        if not image_base64:
            return "(Graph rendering failed — continue writing without it)"

        asset_id = _next_asset_id("graph")
        _generated_assets[asset_id] = {
            "type": parsed_spec.get("concept_type", "graph"),
            "image": image_base64,
            "title": title,
            "description": parsed_spec.get(
                "description", "Visual representation of the concepts discussed."
            ),
        }
        logger.info(f"[Agent Tool] Created graph '{title}' → {asset_id}")

        return f"[GENERATED_GRAPH:{asset_id}]"

    except json.JSONDecodeError as e:
        logger.error(f"Graph spec JSON parse error: {e}")
        return f"(Invalid graph spec JSON: {e})"
    except Exception as e:
        logger.error(f"Graph creation error: {e}")
        return f"(Graph creation error: {e})"


# --- Create Table ---
def tool_create_table(title: str, columns: str, rows: str) -> str:
    """Create a formatted comparison table with structured data."""
    try:
        col_list = [c.strip() for c in columns.split("|")]
        row_list = []
        for row_str in rows.split(";"):
            cells = [c.strip() for c in row_str.strip().split("|")]
            if cells and cells[0]:
                row_list.append(cells)

        if not col_list or not row_list:
            return "(Table must have columns and rows)"

        asset_id = _next_asset_id("table")
        _generated_assets[asset_id] = {
            "type": "table",
            "title": title,
            "description": f"Table: {title}",
            "columns": col_list,
            "rows": row_list,
        }
        logger.info(f"[Agent Tool] Created table '{title}' → {asset_id}")

        return f"[GENERATED_TABLE:{asset_id}]"

    except Exception as e:
        logger.error(f"Table creation error: {e}")
        return f"(Table creation error: {e})"


# ---------------------------------------------------------------------------
# OpenAI tool definitions (JSON schema for function calling)
# ---------------------------------------------------------------------------
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": (
                "Search the web for current events, real-world examples, "
                "recent data, or up-to-date information to enrich educational "
                "content. Use this when you need current real-world examples, "
                "recent statistics, news events that illustrate a principle, "
                "or case studies."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "A specific search query "
                            '(e.g. "US trade deficit 2024 examples")'
                        ),
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_textbook",
            "description": (
                "Retrieve authoritative textbook content from the knowledge "
                "base. Use this when you need precise definitions, theoretical "
                "frameworks, textbook-quality explanations, or authoritative "
                "content to base your writing on."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": (
                            "The specific topic to search for "
                            '(e.g. "production possibilities curve efficiency")'
                        ),
                    }
                },
                "required": ["topic"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_graph",
            "description": (
                "Create an educational graph or chart by providing a full "
                "rendering specification as JSON. You MUST call this tool "
                "when the content involves visual concepts like curves, "
                "relationships between variables, trade-offs, or trends. "
                "You control every detail of the graph — axes, curves, "
                "key points, annotations, and shaded regions."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "A clear title for the graph.",
                    },
                    "spec": {
                        "type": "string",
                        "description": (
                            "A JSON string with the full rendering spec. Schema:\n"
                            "{\n"
                            '  "chart_type": "line_chart|bar_chart|grouped_bar|scatter|area_chart",\n'
                            '  "description": "What this visualization demonstrates",\n'
                            '  "palette": "default|warm|cool|nature|pastel",\n'
                            '  "x_axis": {"label": "X label", "min": 0, "max": 100},\n'
                            '  "y_axis": {"label": "Y label", "min": 0, "max": 100},\n'
                            '  "series": [\n'
                            "    {\n"
                            '      "label": "Series name",\n'
                            '      "shape": "linear|quadratic|exponential_growth|exponential_decay|logarithmic|inverse|sigmoid|step|concave_frontier|constant",\n'
                            '      "direction": "accelerating|decelerating|u_shape|inverted_u (only for quadratic)",\n'
                            '      "y_start": 10,\n'
                            '      "y_end": 90,\n'
                            '      "style": "solid|dashed|dotted",\n'
                            '      "fill_to_zero": false\n'
                            "    }\n"
                            "  ],\n"
                            '  "key_points": [\n'
                            '    {"label": "Point", "x_fraction": 0.5, "on_series": 0, "style": "dot|star|diamond"}\n'
                            "  ],\n"
                            '  "intersections": [\n'
                            '    {"series_a": 0, "series_b": 1, "label": "Equilibrium"}\n'
                            "  ],\n"
                            '  "shaded_regions": [\n'
                            '    {"between": [0, 1], "x_start_frac": 0.0, "x_end_frac": 1.0, "label": "Region", "alpha": 0.15}\n'
                            "  ],\n"
                            '  "annotations": [\n'
                            '    {"text": "Note", "x_fraction": 0.5, "y_fraction": 0.8}\n'
                            "  ]\n"
                            "}\n\n"
                            "SHAPES:\n"
                            "- concave_frontier: bowed-out boundary (quarter-ellipse), perfect for PPC/PPF curves\n"
                            "- linear: straight line\n"
                            "- quadratic: parabola (use direction: accelerating/decelerating/u_shape/inverted_u)\n"
                            "- exponential_growth/decay, logarithmic, inverse, sigmoid, step, constant\n\n"
                            "y_start = value at LEFT edge, y_end = value at RIGHT edge.\n"
                            "For concave_frontier: y_start = max Y (top), y_end = 0 (right end).\n\n"
                            "For bar_chart/grouped_bar, replace series with:\n"
                            '  "categories": ["A", "B", "C"],\n'
                            '  "series": [{"label": "Group", "values": [30, 50, 70]}]'
                        ),
                    },
                },
                "required": ["title", "spec"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_table",
            "description": (
                "Create a formatted comparison table rendered as an image. "
                "You MUST call this tool when the content involves side-by-side "
                "comparisons, numerical data in tabular form, or categorized "
                "information that is clearer as a table."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": (
                            "Title for the table "
                            '(e.g. "Comparative Advantage: Country A vs B")'
                        ),
                    },
                    "columns": {
                        "type": "string",
                        "description": (
                            "Pipe-separated column headers. "
                            'Example: "Country|Good X (units/hr)|Good Y (units/hr)|OC of Good X"'
                        ),
                    },
                    "rows": {
                        "type": "string",
                        "description": (
                            "Semicolon-separated rows, each with pipe-separated "
                            "values. Example: "
                            '"Country A|10|5|0.5 Good Y;Country B|4|8|2 Good Y"'
                        ),
                    },
                },
                "required": ["title", "columns", "rows"],
            },
        },
    },
]

# ---------------------------------------------------------------------------
# Subject-specific graph examples
# ---------------------------------------------------------------------------
GRAPH_EXAMPLES = {
    "economics": """
Example — Production Possibilities Curve:
{{
  "chart_type": "line_chart",
  "description": "PPC showing trade-off between Good X and Good Y",
  "palette": "cool",
  "x_axis": {{"label": "Good X (units)", "min": 0, "max": 50}},
  "y_axis": {{"label": "Good Y (units)", "min": 0, "max": 40}},
  "series": [
    {{"label": "PPC", "shape": "concave_frontier", "y_start": 40, "y_end": 0, "style": "solid"}}
  ],
  "key_points": [
    {{"label": "Efficient", "x_fraction": 0.5, "on_series": 0, "style": "dot"}}
  ]
}}

Example — Supply and Demand:
{{
  "chart_type": "line_chart",
  "description": "Supply and demand curves with equilibrium",
  "x_axis": {{"label": "Quantity", "min": 0, "max": 100}},
  "y_axis": {{"label": "Price ($)", "min": 0, "max": 100}},
  "series": [
    {{"label": "Demand", "shape": "linear", "y_start": 90, "y_end": 10, "style": "solid"}},
    {{"label": "Supply", "shape": "linear", "y_start": 10, "y_end": 90, "style": "solid"}}
  ],
  "intersections": [{{"series_a": 0, "series_b": 1, "label": "Equilibrium"}}]
}}

SUBJECT-SPECIFIC RULES:
- For PPC curves: use "concave_frontier" shape
- For supply/demand: demand slopes DOWN, supply slopes UP
- Mark equilibrium points at intersections
""",
    "biology": """
Example — Enzyme Kinetics (Michaelis-Menten):
{{
  "chart_type": "line_chart",
  "description": "Enzyme reaction rate vs substrate concentration",
  "palette": "nature",
  "x_axis": {{"label": "Substrate Concentration [S]", "min": 0, "max": 100}},
  "y_axis": {{"label": "Reaction Rate (V)", "min": 0, "max": 100}},
  "series": [
    {{"label": "Reaction Rate", "shape": "logarithmic", "y_start": 0, "y_end": 90, "style": "solid"}}
  ],
  "annotations": [
    {{"text": "Vmax", "x_fraction": 0.9, "y_fraction": 0.95}},
    {{"text": "Km", "x_fraction": 0.3, "y_fraction": 0.5}}
  ]
}}

Example — Population Growth:
{{
  "chart_type": "line_chart",
  "description": "Logistic population growth over time",
  "palette": "nature",
  "x_axis": {{"label": "Time", "min": 0, "max": 100}},
  "y_axis": {{"label": "Population Size", "min": 0, "max": 100}},
  "series": [
    {{"label": "Population", "shape": "sigmoid", "y_start": 5, "y_end": 95, "style": "solid"}}
  ],
  "annotations": [
    {{"text": "Carrying Capacity (K)", "x_fraction": 0.8, "y_fraction": 0.95}}
  ]
}}

SUBJECT-SPECIFIC RULES:
- Use "logarithmic" for saturation curves (enzyme kinetics)
- Use "sigmoid" for logistic growth
- Use "exponential_growth" for J-shaped population curves
""",
    "physics": """
Example — Motion (Position vs Time):
{{
  "chart_type": "line_chart",
  "description": "Position of object under constant acceleration",
  "palette": "cool",
  "x_axis": {{"label": "Time (s)", "min": 0, "max": 10}},
  "y_axis": {{"label": "Position (m)", "min": 0, "max": 100}},
  "series": [
    {{"label": "Position", "shape": "quadratic", "direction": "accelerating", "y_start": 0, "y_end": 100, "style": "solid"}}
  ]
}}

Example — Velocity vs Time:
{{
  "chart_type": "line_chart",
  "description": "Velocity under constant acceleration",
  "palette": "cool",
  "x_axis": {{"label": "Time (s)", "min": 0, "max": 10}},
  "y_axis": {{"label": "Velocity (m/s)", "min": 0, "max": 50}},
  "series": [
    {{"label": "Velocity", "shape": "linear", "y_start": 0, "y_end": 50, "style": "solid"}}
  ],
  "shaded_regions": [
    {{"between": [0, "x_axis"], "x_start_frac": 0, "x_end_frac": 1, "label": "Displacement", "alpha": 0.2}}
  ]
}}

SUBJECT-SPECIFIC RULES:
- Use "quadratic" for constant acceleration motion
- Use "linear" for constant velocity or uniform acceleration
- Area under v-t curve represents displacement
""",
    "chemistry": """
Example — Reaction Rate vs Concentration:
{{
  "chart_type": "line_chart",
  "description": "First-order reaction concentration over time",
  "palette": "warm",
  "x_axis": {{"label": "Time (s)", "min": 0, "max": 100}},
  "y_axis": {{"label": "Concentration (M)", "min": 0, "max": 100}},
  "series": [
    {{"label": "[Reactant]", "shape": "exponential_decay", "y_start": 100, "y_end": 10, "style": "solid"}}
  ],
  "annotations": [
    {{"text": "Half-life", "x_fraction": 0.3, "y_fraction": 0.55}}
  ]
}}

Example — Titration Curve:
{{
  "chart_type": "line_chart",
  "description": "pH during acid-base titration",
  "palette": "warm",
  "x_axis": {{"label": "Volume of Titrant (mL)", "min": 0, "max": 50}},
  "y_axis": {{"label": "pH", "min": 0, "max": 14}},
  "series": [
    {{"label": "pH", "shape": "sigmoid", "y_start": 2, "y_end": 12, "style": "solid"}}
  ],
  "key_points": [
    {{"label": "Equivalence Point", "x_fraction": 0.5, "on_series": 0, "style": "dot"}}
  ]
}}

SUBJECT-SPECIFIC RULES:
- Use "exponential_decay" for first-order reactions
- Use "sigmoid" for titration curves
- Mark half-life and equivalence points
""",
    "default": """
Example — Linear Relationship:
{{
  "chart_type": "line_chart",
  "description": "Linear relationship between X and Y",
  "x_axis": {{"label": "X Variable", "min": 0, "max": 100}},
  "y_axis": {{"label": "Y Variable", "min": 0, "max": 100}},
  "series": [
    {{"label": "Data", "shape": "linear", "y_start": 10, "y_end": 90, "style": "solid"}}
  ]
}}

Example — Exponential Growth:
{{
  "chart_type": "line_chart",
  "description": "Exponential growth pattern",
  "x_axis": {{"label": "X", "min": 0, "max": 100}},
  "y_axis": {{"label": "Y", "min": 0, "max": 100}},
  "series": [
    {{"label": "Growth", "shape": "exponential_growth", "y_start": 5, "y_end": 95, "style": "solid"}}
  ]
}}
"""
}

def get_graph_examples(subject_code: str) -> str:
    """Get subject-specific graph examples for the prompt."""
    # Map subject codes to categories
    subject_map = {
        "micro": "economics",
        "macro": "economics",
        "biology": "biology",
        "physics": "physics",
        "chemistry": "chemistry",
    }
    category = subject_map.get(subject_code, "default")
    return GRAPH_EXAMPLES.get(category, GRAPH_EXAMPLES["default"])


# ---------------------------------------------------------------------------
# Agent system prompt
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are an expert educational content writer creating a chapter for an AP-level textbook.

CHAPTER: {chapter_number}: {chapter_title}
SUBJECT: {subject}

TOPICS TO COVER (ONLY these — nothing outside scope):
{chapter_topics}

═══════════════════════════════════════════════════════
YOUR TASK HAS THREE PHASES. You MUST complete ALL three.

══ PHASE 1: RESEARCH ══
Before writing anything, call these tools to gather information:
  • search_web — call 1-2 times to get current real-world examples
  • query_textbook — call once to get authoritative academic content

After calling research tools, you will receive their results. Then proceed to Phase 2.

══ PHASE 2: CREATE VISUALIZATIONS ══
After research, you MUST create visual aids BEFORE writing the chapter:
  • create_graph — you provide a FULL JSON rendering specification (see below).
    You MUST call this at least once. Be PRECISE about axis ranges, curve shapes,
    and key points — you are directly controlling the rendering.
  • create_table — call this for any numerical comparisons or tabular data.

Each tool returns a placeholder tag like [GENERATED_GRAPH:graph_1].
Save these tags — you MUST include them in your chapter text.

═══ GRAPH SPEC REFERENCE ═══
When calling create_graph, provide a "spec" parameter as a JSON string.
Available shapes for series:
  • concave_frontier — bowed-out quarter-ellipse (trade-off curves, PPCs)
  • linear — straight line from y_start to y_end
  • quadratic — parabola. Directions: accelerating, decelerating, u_shape, inverted_u
  • exponential_growth, exponential_decay, logarithmic, inverse, sigmoid, step, constant

{graph_examples}

ACCURACY RULES FOR GRAPHS:
- Set axis ranges to match the REAL numerical values for the concept.
- Use y_start and y_end to control the EXACT start and end values of curves.
- Mark key points at CORRECT positions on the curve.
- Use shaded_regions to highlight important areas.

══ PHASE 3: WRITE THE CHAPTER ══
Only after completing Phases 1 and 2, write the full chapter with this structure:

1. ## Introduction
   Write 2-3 paragraphs introducing the chapter's concepts.

2. Main sections (2-3 sections): ## [Section Title]
   Write 2-4 paragraphs per section, 3-5 sentences each.
   Use **bold** for key terms on first introduction.
   Include specific examples from your research.
   Place [GENERATED_GRAPH:...] or [GENERATED_TABLE:...] placeholders INLINE
   in the text, immediately after the paragraph that references them.
   Do NOT group all visuals in one section.

   CRITICAL - TEACH THE METHOD, NOT JUST THE CONCEPT:
   For any concept that involves calculation or analysis, you MUST teach students HOW to do it:

   a) State the FORMULA or METHOD clearly:
      "**Opportunity Cost Formula:** Opportunity Cost = Units of Good Given Up ÷ Units of Good Gained"

   b) Provide a CONCRETE worked example with real numbers:
      "Suppose a factory can produce either 200 cars or 400 trucks. If they choose to make
      100 more cars (going from 100 to 200), they must give up 200 trucks (going from 400 to 200).
      The opportunity cost = 200 trucks ÷ 100 cars = **2 trucks per car**."

   c) Explain HOW TO READ tables/graphs for these calculations:
      "To find opportunity cost from a production table: identify what you gain (change in one good)
      and what you give up (change in the other good), then divide."

   Students should be able to solve quiz problems after reading your explanation.

3. ## Review Questions
   Write 4 AP-style practice questions:
   **Question 1:** [question]
   A) [option]  B) [option]  C) [option]  D) [option]
   **Answer:** [letter] - [detailed explanation with math if applicable]

4. ## Summary
   Start with "**Key Takeaways:**" and write 2-3 paragraphs.

═══════════════════════════════════════════════════════
CRITICAL RULES:
- You MUST call create_graph at least once. Do NOT skip visualizations.
- Include the exact placeholder tags returned by create_graph/create_table in your text.
- Place placeholders INLINE after the paragraph that references them, NOT all in one section.
- Use ## for section headings only. Do NOT use ### or other heading levels.
- Do NOT use markdown headings inside tool call arguments.
- Stay strictly within the chapter's topic boundaries.
"""

# The nudge message sent if the agent hasn't created any graphs/tables
VISUAL_NUDGE = (
    "You have not yet called create_graph or create_table. "
    "You MUST create at least one visualization before writing the chapter. "
    "Call create_graph now with a description of the most important visual "
    "concept in this chapter. Then call create_table if there are any "
    "comparisons or data that should be shown in a table."
)


# ---------------------------------------------------------------------------
# Tool dispatcher — executes a tool call and returns the result string
# ---------------------------------------------------------------------------
async def _execute_tool(name: str, arguments: dict) -> str:
    """Dispatch a tool call to the appropriate function."""
    if name == "search_web":
        return tool_search_web(arguments.get("query", ""))
    elif name == "query_textbook":
        return await tool_query_textbook(arguments.get("topic", ""))
    elif name == "create_graph":
        return await tool_create_graph(
            arguments.get("title", ""),
            arguments.get("spec", "{}"),
        )
    elif name == "create_table":
        return tool_create_table(
            arguments.get("title", ""),
            arguments.get("columns", ""),
            arguments.get("rows", ""),
        )
    else:
        return f"(Unknown tool: {name})"


# ---------------------------------------------------------------------------
# Main generator class — custom agent loop
# ---------------------------------------------------------------------------
class AgenticTextbookGenerator:
    def __init__(self):
        self.client = AsyncOpenAI()
        self.model = "gpt-4o"

    async def generate_chapter(
        self,
        subject: str,
        chapter_number: str,
        chapter_title: str,
        subject_code: str,
    ) -> Tuple[List[str], Dict[str, Dict[str, Any]]]:
        """
        Generate a full chapter using the agentic approach with a custom loop.

        Returns:
            (paragraphs, graphs_dict) — same shape as the old pipeline
        """
        global _current_subject
        _reset_assets()
        _current_subject = subject_code

        # Get chapter-specific topics from TOC
        from .helpers import get_chapter_specific_topics
        chapter_topics = get_chapter_specific_topics(
            chapter_number, chapter_title, subject_code
        )

        # Build the system prompt
        # Get subject-specific graph examples
        graph_examples = get_graph_examples(subject_code)

        system_content = SYSTEM_PROMPT.format(
            chapter_number=chapter_number,
            chapter_title=chapter_title,
            subject=subject,
            chapter_topics=chapter_topics,
            graph_examples=graph_examples,
        )

        messages = [
            {"role": "system", "content": system_content},
            {
                "role": "user",
                "content": (
                    f"Write chapter {chapter_number}: {chapter_title}. "
                    "Start by calling search_web and query_textbook to gather "
                    "information, then create visualizations with create_graph "
                    "and/or create_table, and finally write the complete chapter."
                ),
            },
        ]

        logger.info(
            f"[Agent] Starting generation for {chapter_number}: {chapter_title}"
        )

        max_iterations = 25
        iteration = 0
        visual_nudge_sent = False
        final_text = ""

        while iteration < max_iterations:
            iteration += 1
            logger.info(f"[Agent] Iteration {iteration}/{max_iterations}")

            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=TOOL_DEFINITIONS,
                    tool_choice="auto",
                    temperature=0.3,
                    max_tokens=8000,
                )
            except Exception as e:
                logger.error(f"[Agent] OpenAI API error: {e}")
                break

            choice = response.choices[0]
            message = choice.message

            # Add the assistant message to the conversation
            # Build a clean dict — OpenAI SDK v1+ uses Pydantic models
            assistant_msg: Dict[str, Any] = {
                "role": "assistant",
                "content": message.content or "",
            }
            if message.tool_calls:
                assistant_msg["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in message.tool_calls
                ]
            messages.append(assistant_msg)

            # If the model wants to call tools, execute them
            if message.tool_calls:
                for tc in message.tool_calls:
                    fn_name = tc.function.name
                    try:
                        fn_args = json.loads(tc.function.arguments)
                    except json.JSONDecodeError:
                        fn_args = {}

                    logger.info(
                        f"[Agent] Tool call: {fn_name}("
                        f"{str(fn_args)[:120]})"
                    )

                    result = await _execute_tool(fn_name, fn_args)

                    # Truncate very long results to keep context manageable
                    if len(result) > 3000:
                        result = result[:3000] + "\n...(truncated)"

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result,
                    })

                # Continue the loop to let the model process tool results
                continue

            # No tool calls — the model produced a text response
            if message.content:
                final_text = message.content

            # Check: did the agent create any visuals?
            has_visuals = len(_generated_assets) > 0
            has_placeholders = bool(
                re.search(r"\[GENERATED_(?:GRAPH|TABLE):\w+\]", final_text)
            )

            if has_visuals or has_placeholders:
                # Agent created visuals and included them — we're done
                logger.info(
                    f"[Agent] Finished with {len(_generated_assets)} assets"
                )
                break

            if not visual_nudge_sent:
                # Agent wrote text but didn't create any visuals.
                # Nudge it to create them.
                visual_nudge_sent = True
                logger.info(
                    "[Agent] No visuals found — sending nudge to create them"
                )
                messages.append({
                    "role": "user",
                    "content": VISUAL_NUDGE,
                })
                # Clear final_text so the agent rewrites with visuals
                final_text = ""
                continue
            else:
                # Already nudged once — accept what we have
                logger.warning(
                    "[Agent] Still no visuals after nudge — accepting output"
                )
                break

        if not final_text:
            logger.error("[Agent] No output produced")
            final_text = (
                f"## Introduction\n\n"
                f"This chapter covers {chapter_title}.\n\n"
                f"## Summary\n\n"
                f"**Key Takeaways:** Content generation encountered an issue. "
                f"Please try regenerating this chapter."
            )

        logger.info(f"[Agent] Raw output length: {len(final_text)} chars")
        logger.info(
            f"[Agent] Generated {len(_generated_assets)} assets "
            f"(graphs/tables) in {iteration} iterations"
        )

        # Post-process into the expected format
        paragraphs, graphs_dict = self._post_process(final_text)

        logger.info(
            f"[Agent] Final: {len(paragraphs)} paragraphs, "
            f"{len(graphs_dict)} graphs/tables"
        )
        return paragraphs, graphs_dict

    def _post_process(
        self, raw_output: str
    ) -> Tuple[List[str], Dict[str, Dict[str, Any]]]:
        """
        Convert the agent's raw text output into:
          - paragraphs: List[str] with ## headings (same as old pipeline)
          - graphs_dict: Dict[str, asset_data] keyed by paragraph index
        """
        # Split on double newlines to get raw chunks
        chunks = re.split(r"\n{2,}", raw_output.strip())
        raw_paragraphs = [c.strip() for c in chunks if c.strip()]

        # Separate headings from body text when joined by single newlines,
        # and normalize ### headings to ##.
        paragraphs: List[str] = []
        for para in raw_paragraphs:
            if "\n" not in para:
                # Single line — just normalize heading level
                if para.startswith("### "):
                    para = "## " + para[4:]
                paragraphs.append(para)
                continue

            # Multi-line chunk: split on heading boundaries
            lines = para.split("\n")
            buffer: List[str] = []
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("## ") or stripped.startswith("### "):
                    # Flush preceding body text
                    if buffer:
                        text = "\n".join(buffer).strip()
                        if text:
                            paragraphs.append(text)
                        buffer = []
                    # Normalize ### → ##
                    if stripped.startswith("### "):
                        stripped = "## " + stripped[4:]
                    paragraphs.append(stripped)
                else:
                    buffer.append(line)
            if buffer:
                text = "\n".join(buffer).strip()
                if text:
                    paragraphs.append(text)

        # Find and map asset placeholders to paragraph indices
        graphs_dict: Dict[str, Dict[str, Any]] = {}
        placeholder_re = re.compile(
            r"\[GENERATED_(?:GRAPH|TABLE):(\w+)\]"
        )

        for i, para in enumerate(paragraphs):
            for match in placeholder_re.finditer(para):
                asset_id = match.group(1)
                if asset_id in _generated_assets:
                    graphs_dict[str(i)] = _generated_assets[asset_id]

            # Remove placeholder tags from paragraph text
            paragraphs[i] = placeholder_re.sub("", para).strip()

        # Remove empty paragraphs that were only placeholders, but carry
        # their graph assignments forward to the nearest non-empty paragraph.
        # Build a list of (asset, original_index) to distribute.
        asset_queue: List[Dict[str, Any]] = []
        for i, para in enumerate(paragraphs):
            if str(i) in graphs_dict:
                asset_queue.append((graphs_dict[str(i)], i))

        cleaned = []
        new_graphs: Dict[str, Dict[str, Any]] = {}

        # Map original indices to new (cleaned) indices
        old_to_new: Dict[int, int] = {}
        for i, para in enumerate(paragraphs):
            if para:
                old_to_new[i] = len(cleaned)
                cleaned.append(para)

        # Assign each asset to the closest non-empty paragraph
        for asset, orig_idx in asset_queue:
            # Try exact match first
            if orig_idx in old_to_new:
                new_idx = old_to_new[orig_idx]
            else:
                # Placeholder was its own paragraph (now empty).
                # Find the next non-empty paragraph after it.
                new_idx = None
                for j in range(orig_idx + 1, len(paragraphs)):
                    if j in old_to_new:
                        new_idx = old_to_new[j]
                        break
                # If nothing after, use the previous one
                if new_idx is None:
                    for j in range(orig_idx - 1, -1, -1):
                        if j in old_to_new:
                            new_idx = old_to_new[j]
                            break
                if new_idx is None and cleaned:
                    new_idx = len(cleaned) - 1

            if new_idx is not None:
                # If this index is already taken, bump to the next available
                while str(new_idx) in new_graphs and new_idx < len(cleaned) - 1:
                    new_idx += 1
                new_graphs[str(new_idx)] = asset

        # Fallback: if assets were generated but NONE ended up in graphs_dict
        # (agent didn't include placeholder tags at all), attach by section
        if _generated_assets and not new_graphs:
            logger.info(
                f"[Post-process] No placeholders matched — attaching "
                f"{len(_generated_assets)} assets by section detection"
            )
            charts_idx = None
            for i, para in enumerate(cleaned):
                if para.lower().startswith("## charts") or \
                   para.lower().startswith("## chart"):
                    charts_idx = i
                    break

            insert_start = (charts_idx + 1) if charts_idx is not None \
                else max(1, int(len(cleaned) * 0.6))

            for offset, (asset_id, asset_data) in enumerate(
                _generated_assets.items()
            ):
                target_idx = min(insert_start + offset, len(cleaned) - 1)
                new_graphs[str(target_idx)] = asset_data
                logger.info(
                    f"[Post-process] Attached '{asset_data.get('title', asset_id)}'"
                    f" at paragraph {target_idx}"
                )

        return cleaned, new_graphs


# Global instance
agentic_generator = AgenticTextbookGenerator()
