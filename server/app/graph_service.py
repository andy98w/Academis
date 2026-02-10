"""
Universal Graph Generation Service

Generates visually diverse educational graphs for ANY subject by having the LLM
describe visualizations in terms of mathematical shapes and visual properties.
No domain-specific graph templates — works for economics, biology, physics, chemistry, etc.
"""

import io
import base64
import json
import logging
from typing import Dict, List, Any, Optional
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from langchain_openai import ChatOpenAI
from langchain.schema.output_parser import StrOutputParser
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from .graph_storage import graph_storage

load_dotenv(override=True)
logger = logging.getLogger(__name__)

plt.switch_backend('Agg')

# ---------------------------------------------------------------------------
# Color palettes and styles for visual diversity
# ---------------------------------------------------------------------------
PALETTES = {
    "default": ["#2196F3", "#F44336", "#4CAF50", "#FF9800", "#9C27B0", "#795548"],
    "warm":    ["#E53935", "#FF7043", "#FFB300", "#F4511E", "#D81B60", "#BF360C"],
    "cool":    ["#1E88E5", "#00ACC1", "#00897B", "#3949AB", "#5E35B1", "#0277BD"],
    "nature":  ["#2E7D32", "#558B2F", "#F9A825", "#E65100", "#4E342E", "#33691E"],
    "pastel":  ["#90CAF9", "#EF9A9A", "#A5D6A7", "#FFE082", "#CE93D8", "#FFAB91"],
}

SNS_STYLES = {
    "default": "whitegrid",
    "warm":    "darkgrid",
    "cool":    "whitegrid",
    "nature":  "white",
    "pastel":  "white",
}


class UniversalGraphGenerator:
    def __init__(self):
        self.model = ChatOpenAI(model_name="gpt-4o", temperature=0.2)

    # ==================================================================
    # Public API (unchanged signature)
    # ==================================================================
    async def generate_contextual_graph(
        self, content: str, context_title: str = "", subject: str = ""
    ) -> Optional[Dict[str, Any]]:
        """Analyze content and generate an appropriate graph for any subject."""
        try:
            # Step 1: Quick check — should we visualize?
            analysis = await self._analyze_visualization_need(content, context_title)
            analysis["needs_visualization"] = True  # currently always generate
            if not analysis["needs_visualization"]:
                return None

            # Step 2: Get a rendering-ready visualization spec from the LLM
            spec = await self._extract_visualization_concept(content, context_title, analysis)
            if not spec:
                return None

            # Step 3: Render the graph
            image_base64 = await self._render_graph(spec)
            if not image_base64:
                return None

            # Cache — use the full spec as parameters for unique hashing
            await graph_storage.store_graph(
                spec.get("concept_type", "universal"),
                {"title": spec.get("title", ""), "chart_type": spec.get("chart_type", "")},
                image_base64,
                subject=subject,
                tags=spec.get("tags", ["universal"]),
            )

            return {
                "type": spec.get("concept_type", "relationship"),
                "image": image_base64,
                "title": spec.get("title", "Conceptual Visualization"),
                "description": spec.get(
                    "description",
                    "Visual representation of the concepts discussed.",
                ),
            }

        except Exception as e:
            logger.error(f"Error in universal graph generation: {e}")
            return None

    # ==================================================================
    # Step 1 — decide if visualization is useful
    # ==================================================================
    async def _analyze_visualization_need(
        self, content: str, context_title: str
    ) -> Dict[str, Any]:
        prompt = ChatPromptTemplate.from_template(
            """
Analyze this educational content to determine if it contains concepts
that would benefit from visual representation.

Title: {context_title}
Content: {content}

Look for:
- Relationships between two or more variables/concepts
- Comparisons or trade-offs
- Processes or flows
- Trends, patterns, or changes over time/conditions
- Mathematical or logical relationships
- Abstract concepts that could be made concrete through visualization

Return JSON:
{{
    "needs_visualization": true/false,
    "confidence": 0-100,
    "primary_concepts": ["concept1", "concept2"],
    "relationship_type": "positive/negative/inverse/cyclical/comparative/process/other",
    "reasoning": "explanation"
}}

Be generous — if there are ANY relationships that could be clearer
with a visual aid, say true.
"""
        )

        chain = prompt | self.model | StrOutputParser()
        response = await chain.ainvoke(
            {"content": content[:2000], "context_title": context_title}
        )

        try:
            return json.loads(self._clean_json(response))
        except Exception as e:
            logger.error(f"Failed to parse analysis response: {e}")
            return {"needs_visualization": False}

    # ==================================================================
    # Step 2 — get a rendering-ready spec from the LLM
    # ==================================================================
    async def _extract_visualization_concept(
        self,
        content: str,
        context_title: str,
        analysis: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        prompt = ChatPromptTemplate.from_template(
            """You are a data-visualization designer for an educational platform.
Given the content below, create a COMPLETE rendering specification that
a plotting library can execute directly.

Do NOT write domain-specific code — describe everything in terms of
mathematical shapes and visual properties.

Content: {content}
Title: {context_title}
Analysis: {analysis}

═══════════════════════════════════════════════════════
CHART TYPES (pick the best one):
  line_chart   — one or more curves on a continuous x-axis
  bar_chart    — vertical bars (one group)
  grouped_bar  — side-by-side bars comparing multiple groups
  scatter      — scatter plot for correlation / distribution
  area_chart   — filled area under one or more curves

═══════════════════════════════════════════════════════
MATHEMATICAL SHAPES for each series (line_chart / area_chart / scatter):
  linear              — straight line
  quadratic           — parabola (use direction to pick variant)
  exponential_growth  — slow start, accelerating increase
  exponential_decay   — fast start, then levels off
  logarithmic         — rapid rise that gradually slows
  inverse             — hyperbola (1/x shape)
  sigmoid             — S-curve (logistic)
  step                — sudden jump at midpoint
  concave_frontier    — bowed-out boundary curve (quarter-ellipse),
                        useful for any trade-off or constraint boundary
  constant            — flat horizontal line

DIRECTIONS (only meaningful for "quadratic" shape):
  accelerating  — slow start, fast finish (t²)
  decelerating  — fast start, slow finish (√t)
  u_shape       — high at edges, low at center
  inverted_u    — low at edges, high at center

For all other shapes, direction is ignored — the curve shape is
inherent, and y_start / y_end control whether it goes up or down.

═══════════════════════════════════════════════════════
RETURN THIS JSON (follow the schema exactly):
{{
    "chart_type": "line_chart",
    "title": "Clear descriptive title",
    "description": "What this visualization demonstrates",
    "palette": "default | warm | cool | nature | pastel",
    "x_axis": {{"label": "X-axis label", "min": 0, "max": 100}},
    "y_axis": {{"label": "Y-axis label", "min": 0, "max": 100}},
    "series": [
        {{
            "label": "Series name",
            "shape": "linear",
            "direction": "increasing",
            "y_start": 10,
            "y_end": 90,
            "style": "solid",
            "fill_to_zero": false
        }}
    ],
    "key_points": [
        {{"label": "Point name", "x_fraction": 0.5, "on_series": 0, "style": "dot"}}
    ],
    "intersections": [
        {{"series_a": 0, "series_b": 1, "label": "Equilibrium"}}
    ],
    "shaded_regions": [
        {{"between": [0, 1], "x_start_frac": 0.0, "x_end_frac": 1.0,
          "label": "Region", "alpha": 0.15}}
    ],
    "annotations": [
        {{"text": "Note", "x_fraction": 0.5, "y_fraction": 0.8}}
    ],
    "concept_type": "short keyword",
    "tags": ["keyword1", "keyword2"],
    "parameters": {{}}
}}

For bar_chart / grouped_bar, replace "series" and add "categories":
    "categories": ["Cat A", "Cat B", "Cat C", "Cat D"],
    "series": [
        {{"label": "Group 1", "values": [30, 50, 70, 45]}},
        {{"label": "Group 2", "values": [45, 35, 60, 55]}}
    ]

═══════════════════════════════════════════════════════
y_start / y_end RULES:
• y_start = value of this series at the LEFT edge of the graph
• y_end   = value of this series at the RIGHT edge of the graph
• For u_shape:    y_start = edge values (high), y_end = center value (low)
• For inverted_u: y_start = edge values (low),  y_end = center value (high)
• To make a line go DOWN, just set y_start > y_end.
• IMPORTANT: y_start and y_end MUST be different (except for "constant" shape).
  If they are equal, the line becomes flat/horizontal regardless of shape.
  Ensure at least 20+ units difference for visible curves.

═══════════════════════════════════════════════════════
ANNOTATION RULES:
• Use at most 2 annotations per graph to avoid clutter.
• Space annotations apart — avoid placing multiple at similar x_fraction/y_fraction.
• Keep annotation text SHORT (under 8 words) for readability.
• Place annotations in empty areas of the graph, not over curves or data.

═══════════════════════════════════════════════════════
DESIGN GUIDELINES:
- Use DIVERSE chart types. Bar charts for categorical comparisons,
  line charts for continuous relationships, scatter for distributions.
- Use MULTIPLE series when comparing or contrasting things.
- Choose different mathematical shapes to create VISUALLY DISTINCT graphs.
- Pick a palette that fits the subject (nature→biology, cool→physics,
  warm→social science, pastel→introductory, default→general).
- Mark intersections where series cross — often the key educational point.
- Use shaded_regions to highlight important areas.
- Include 1-3 key_points on important curve features.
- Include 0-2 annotations for context.
- The graph should be self-explanatory to a student.
"""
        )

        chain = prompt | self.model | StrOutputParser()
        response = await chain.ainvoke(
            {
                "content": content[:1500],
                "context_title": context_title,
                "analysis": json.dumps(analysis),
            }
        )

        try:
            return json.loads(self._clean_json(response))
        except Exception as e:
            logger.error(f"Failed to parse visualization spec: {e}")
            return None

    # ==================================================================
    # Step 3 — render the graph
    # ==================================================================
    async def _render_graph(self, spec: Dict[str, Any]) -> Optional[str]:
        try:
            palette_name = spec.get("palette", "default")
            colors = PALETTES.get(palette_name, PALETTES["default"])
            style = SNS_STYLES.get(palette_name, "whitegrid")
            sns.set_style(style)

            fig, ax = plt.subplots(figsize=(10, 7))

            chart_type = spec.get("chart_type", "line_chart")

            if chart_type in ("bar_chart", "grouped_bar"):
                self._plot_bar_chart(ax, spec, colors)
            elif chart_type == "scatter":
                self._plot_scatter(ax, spec, colors)
            else:  # line_chart / area_chart
                self._plot_line_chart(ax, spec, colors)

            ax.set_title(
                spec.get("title", ""),
                fontsize=14,
                fontweight="bold",
                pad=15,
            )
            ax.grid(True, alpha=0.3)

            # Clamp axis limits to the spec's ranges to prevent
            # annotations from stretching the figure
            x_axis = spec.get("x_axis", {})
            y_axis = spec.get("y_axis", {})
            if "min" in x_axis and "max" in x_axis:
                x_lo, x_hi = float(x_axis["min"]), float(x_axis["max"])
                x_margin = (x_hi - x_lo) * 0.05
                ax.set_xlim(x_lo - x_margin, x_hi + x_margin)
            if "min" in y_axis and "max" in y_axis:
                y_lo, y_hi = float(y_axis["min"]), float(y_axis["max"])
                y_margin = (y_hi - y_lo) * 0.08
                ax.set_ylim(y_lo - y_margin, y_hi + y_margin)

            try:
                fig.tight_layout()
            except Exception:
                pass  # tight_layout can fail with many decorations

            return self._fig_to_base64(fig)

        except Exception as e:
            logger.error(f"Error rendering graph: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    # ==================================================================
    # Data generation from mathematical shapes
    # ==================================================================
    def _generate_series_data(
        self, series_spec: Dict, x_min: float, x_max: float, n: int = 200
    ):
        """Return (x_array, y_array) for a single series based on its
        mathematical shape.  All norm curves go 0→1 so that
        y = y_start + (y_end − y_start) × norm  maps cleanly."""

        shape = series_spec.get("shape", "linear")
        direction = series_spec.get("direction", "increasing")
        y_start = float(series_spec.get("y_start", 10))
        y_end = float(series_spec.get("y_end", 90))

        # Prevent flat lines for non-constant shapes when y_start == y_end
        # Add a small difference to make the shape visible
        if shape != "constant" and abs(y_end - y_start) < 0.01:
            # Default to a reasonable range if LLM gave equal values
            y_mid = (y_start + y_end) / 2
            y_start = max(0, y_mid - 20)
            y_end = y_mid + 20
            logger.warning(f"Shape '{shape}' had y_start≈y_end; adjusted to show curve")

        x = np.linspace(x_min, x_max, n)
        t = np.linspace(0, 1, n)  # normalised parameter [0, 1]

        # ------ special cases that handle their own y scaling ----------

        if shape == "concave_frontier":
            # Quarter-ellipse bowed OUTWARD from the origin.
            # For a PPC: y_start = max Y (y-intercept), y_end = 0 (at x-intercept).
            # x goes from x_min to x_max (left to right, monotonically).
            # y goes from y_start (high, left) to y_end (low, right).
            angle = t * np.pi / 2  # 0 → π/2
            x_out = x_min + (x_max - x_min) * np.sin(angle)
            y_out = y_end + (y_start - y_end) * np.cos(angle)
            return x_out, y_out

        if shape == "quadratic" and direction == "u_shape":
            # high at edges (y_start), low at center (y_end)
            norm = 4 * (t - 0.5) ** 2  # 1→0→1
            y = y_end + (y_start - y_end) * norm
            return x, y

        if shape == "quadratic" and direction == "inverted_u":
            # low at edges (y_start), high at center (y_end)
            norm = 1 - 4 * (t - 0.5) ** 2  # 0→1→0
            y = y_start + (y_end - y_start) * norm
            return x, y

        # ------ standard cases: norm ∈ [0, 1], y = y_start + Δy × norm --

        if shape == "linear":
            norm = t

        elif shape == "quadratic":
            if direction == "decelerating":
                norm = 1 - (1 - t) ** 2  # fast start, slow finish
            else:  # accelerating (default)
                norm = t ** 2  # slow start, fast finish

        elif shape == "exponential_growth":
            raw = np.exp(4 * t) - 1
            norm = raw / raw[-1]

        elif shape == "exponential_decay":
            raw = 1 - np.exp(-4 * t)
            norm = raw / raw[-1]

        elif shape == "logarithmic":
            raw = np.log1p(9 * t)
            norm = raw / raw[-1]

        elif shape == "inverse":
            raw = 1 - 1 / (1 + 9 * t)
            norm = raw / raw[-1]

        elif shape == "sigmoid":
            raw = 1 / (1 + np.exp(-12 * (t - 0.5)))
            norm = (raw - raw[0]) / (raw[-1] - raw[0])

        elif shape == "step":
            norm = np.where(t < 0.5, 0.0, 1.0)

        elif shape == "constant":
            norm = np.full_like(t, 0.5)

        else:
            norm = t  # fallback to linear

        y = y_start + (y_end - y_start) * norm
        return x, y

    # ==================================================================
    # Chart type renderers
    # ==================================================================
    def _plot_line_chart(self, ax, spec: Dict, colors: List[str]):
        """Render line_chart or area_chart with multiple series."""
        x_axis = spec.get("x_axis", {})
        y_axis = spec.get("y_axis", {})
        x_min = float(x_axis.get("min", 0))
        x_max = float(x_axis.get("max", 100))

        series_list = spec.get("series", [])
        all_series_data: List = []

        style_map = {"solid": "-", "dashed": "--", "dotted": ":"}

        for i, s in enumerate(series_list):
            x, y = self._generate_series_data(s, x_min, x_max)
            # Sort by x so intersection / region logic always works
            sort_idx = np.argsort(x)
            x, y = x[sort_idx], y[sort_idx]
            all_series_data.append((x, y))

            color = colors[i % len(colors)]
            ls = style_map.get(s.get("style", "solid"), "-")
            ax.plot(
                x, y,
                color=color,
                linestyle=ls,
                linewidth=2.5,
                label=s.get("label", f"Series {i + 1}"),
                alpha=0.9,
            )

            if s.get("fill_to_zero") or spec.get("chart_type") == "area_chart":
                ax.fill_between(x, 0, y, color=color, alpha=0.15)

        # Intersections
        for inter in spec.get("intersections", []):
            self._mark_intersection(ax, all_series_data, inter)

        # Shaded regions
        for region in spec.get("shaded_regions", []):
            self._shade_region(ax, all_series_data, region, colors, x_min, x_max)

        # Key points
        for kp in spec.get("key_points", []):
            self._mark_key_point(ax, all_series_data, kp, colors, x_min, x_max)

        # Annotations
        y_min = float(y_axis.get("min", 0))
        y_max_val = float(y_axis.get("max", 100))
        for i, ann in enumerate(spec.get("annotations", [])):
            self._add_annotation(ax, ann, x_min, x_max, y_min, y_max_val, index=i)

        ax.set_xlabel(x_axis.get("label", ""), fontsize=12)
        ax.set_ylabel(y_axis.get("label", ""), fontsize=12)

        if len(series_list) > 1:
            ax.legend(loc="best", fontsize=10)

    def _plot_bar_chart(self, ax, spec: Dict, colors: List[str]):
        """Render bar_chart or grouped_bar."""
        categories = spec.get("categories", ["A", "B", "C"])
        series_list = spec.get("series", [])
        chart_type = spec.get("chart_type", "bar_chart")

        # Add left margin so bars don't touch the y-axis
        x_pos = np.arange(len(categories))
        n_groups = max(len(series_list), 1)
        bar_width = 0.7 / n_groups

        for i, s in enumerate(series_list):
            values = s.get("values", [0] * len(categories))
            offset = (
                (i - n_groups / 2 + 0.5) * bar_width
                if chart_type == "grouped_bar"
                else 0
            )
            color = colors[i % len(colors)]
            width = bar_width if chart_type == "grouped_bar" else 0.6

            bars = ax.bar(
                x_pos + offset,
                values,
                width,
                label=s.get("label", f"Group {i + 1}"),
                color=color,
                alpha=0.85,
                edgecolor="white",
            )
            # Value labels on top of bars
            for bar_obj, val in zip(bars, values):
                ax.text(
                    bar_obj.get_x() + bar_obj.get_width() / 2,
                    bar_obj.get_height() + 1,
                    f"{val}",
                    ha="center",
                    va="bottom",
                    fontsize=9,
                    fontweight="bold",
                )

        ax.set_xticks(x_pos)
        ax.set_xticklabels(categories, fontsize=11)
        # Add margin on left so bars don't touch y-axis
        ax.set_xlim(-0.6, len(categories) - 0.4)
        ax.set_xlabel(spec.get("x_axis", {}).get("label", ""), fontsize=12)
        ax.set_ylabel(spec.get("y_axis", {}).get("label", ""), fontsize=12)

        # Annotations (bar charts can have them too)
        for i, ann in enumerate(spec.get("annotations", [])):
            self._add_annotation(
                ax, ann,
                0, len(categories) - 1,
                0, max(max(s.get("values", [0])) for s in series_list) * 1.2,
                index=i,
            )

        if n_groups > 1:
            ax.legend(loc="best", fontsize=10)

    def _plot_scatter(self, ax, spec: Dict, colors: List[str]):
        """Render scatter plot with optional trend lines."""
        x_axis = spec.get("x_axis", {})
        x_min = float(x_axis.get("min", 0))
        x_max = float(x_axis.get("max", 100))

        series_list = spec.get("series", [])
        all_series_data: List = []
        markers = ["o", "s", "^", "D", "v"]

        for i, s in enumerate(series_list):
            x, y = self._generate_series_data(s, x_min, x_max, n=60)
            sort_idx = np.argsort(x)
            x, y = x[sort_idx], y[sort_idx]

            # Add scatter noise
            noise_scale = abs(float(s.get("y_end", 90)) - float(s.get("y_start", 10))) * 0.08
            y_noisy = y + np.random.normal(0, max(noise_scale, 1), len(y))
            all_series_data.append((x, y))

            color = colors[i % len(colors)]
            ax.scatter(
                x, y_noisy,
                color=color,
                alpha=0.6,
                s=40,
                marker=markers[i % len(markers)],
                label=s.get("label", f"Series {i + 1}"),
                edgecolors="white",
                linewidth=0.5,
            )
            # Trend line
            ax.plot(x, y, color=color, alpha=0.4, linewidth=1.5, linestyle="--")

        # Key points
        for kp in spec.get("key_points", []):
            self._mark_key_point(ax, all_series_data, kp, colors, x_min, x_max)

        # Annotations
        y_axis = spec.get("y_axis", {})
        for i, ann in enumerate(spec.get("annotations", [])):
            self._add_annotation(
                ax, ann, x_min, x_max,
                float(y_axis.get("min", 0)),
                float(y_axis.get("max", 100)),
                index=i,
            )

        ax.set_xlabel(x_axis.get("label", ""), fontsize=12)
        ax.set_ylabel(spec.get("y_axis", {}).get("label", ""), fontsize=12)

        if len(series_list) > 1:
            ax.legend(loc="best", fontsize=10)

    # ==================================================================
    # Annotation helpers
    # ==================================================================
    def _mark_intersection(self, ax, all_series_data: List, inter: Dict):
        """Find and mark where two series cross."""
        try:
            idx_a = inter.get("series_a", 0)
            idx_b = inter.get("series_b", 1)
            if idx_a >= len(all_series_data) or idx_b >= len(all_series_data):
                return

            x_a, y_a = all_series_data[idx_a]
            x_b, y_b = all_series_data[idx_b]

            # Interpolate both onto a common evenly-spaced x grid
            lo = max(x_a.min(), x_b.min())
            hi = min(x_a.max(), x_b.max())
            if lo >= hi:
                return
            x_common = np.linspace(lo, hi, 500)
            y_a_c = np.interp(x_common, x_a, y_a)
            y_b_c = np.interp(x_common, x_b, y_b)

            diff = y_a_c - y_b_c
            sign_changes = np.where(np.diff(np.sign(diff)))[0]
            if len(sign_changes) == 0:
                return

            # Take the first crossing, linearly interpolate
            i = sign_changes[0]
            denom = abs(diff[i]) + abs(diff[i + 1])
            if denom == 0:
                return
            frac = abs(diff[i]) / denom
            x_cross = x_common[i] + frac * (x_common[i + 1] - x_common[i])
            y_cross = y_a_c[i] + frac * (y_a_c[i + 1] - y_a_c[i])

            ax.scatter(
                x_cross, y_cross,
                s=120, color="#4CAF50", zorder=10,
                edgecolors="black", linewidth=1.5,
            )
            label_text = inter.get("label", "Intersection")
            ax.annotate(
                label_text,
                (x_cross, y_cross),
                xytext=(15, 15),
                textcoords="offset points",
                fontsize=10,
                fontweight="bold",
                bbox=dict(
                    boxstyle="round,pad=0.3",
                    facecolor="white",
                    edgecolor="#4CAF50",
                    alpha=0.9,
                ),
                arrowprops=dict(arrowstyle="->", color="#4CAF50", lw=1.5),
            )

            # Dashed guide lines to axes
            ax.axhline(y=y_cross, color="gray", linestyle=":", alpha=0.5, linewidth=0.8)
            ax.axvline(x=x_cross, color="gray", linestyle=":", alpha=0.5, linewidth=0.8)

        except Exception as e:
            logger.debug(f"Could not mark intersection: {e}")

    def _shade_region(
        self,
        ax,
        all_series_data: List,
        region: Dict,
        colors: List[str],
        x_min: float,
        x_max: float,
    ):
        """Shade area between two series."""
        try:
            between = region.get("between", [0, 1])
            if len(between) < 2:
                return
            idx_a, idx_b = between[0], between[1]
            if idx_a >= len(all_series_data) or idx_b >= len(all_series_data):
                return

            x_a, y_a = all_series_data[idx_a]
            x_b, y_b = all_series_data[idx_b]

            # Common x grid
            lo = max(x_a.min(), x_b.min())
            hi = min(x_a.max(), x_b.max())
            x_common = np.linspace(lo, hi, 300)
            y_a_c = np.interp(x_common, x_a, y_a)
            y_b_c = np.interp(x_common, x_b, y_b)

            x_start = x_min + (x_max - x_min) * region.get("x_start_frac", 0)
            x_end = x_min + (x_max - x_min) * region.get("x_end_frac", 1)
            mask = (x_common >= x_start) & (x_common <= x_end)

            alpha = region.get("alpha", 0.15)
            color = colors[idx_a % len(colors)]
            ax.fill_between(
                x_common[mask],
                y_a_c[mask],
                y_b_c[mask],
                alpha=alpha,
                color=color,
                label=region.get("label", ""),
            )
        except Exception as e:
            logger.debug(f"Could not shade region: {e}")

    def _mark_key_point(
        self,
        ax,
        all_series_data: List,
        kp: Dict,
        colors: List[str],
        x_min: float,
        x_max: float,
    ):
        """Mark an important point on a series."""
        try:
            series_idx = kp.get("on_series", 0)
            if series_idx >= len(all_series_data):
                return

            x_data, y_data = all_series_data[series_idx]
            x_frac = kp.get("x_fraction", 0.5)
            target_x = x_min + (x_max - x_min) * x_frac
            idx = int(np.argmin(np.abs(x_data - target_x)))
            px, py = x_data[idx], y_data[idx]

            style_map = {"dot": "o", "star": "*", "diamond": "D"}
            marker = style_map.get(kp.get("style", "dot"), "o")
            color = kp.get("color_override") or colors[series_idx % len(colors)]

            ax.scatter(
                px, py,
                s=100, marker=marker, color=color,
                zorder=8, edgecolors="black", linewidth=1,
            )
            if kp.get("label"):
                ax.annotate(
                    kp["label"],
                    (px, py),
                    xytext=(10, 10),
                    textcoords="offset points",
                    fontsize=9,
                    bbox=dict(
                        boxstyle="round,pad=0.2",
                        facecolor="white",
                        alpha=0.8,
                    ),
                )
        except Exception as e:
            logger.debug(f"Could not mark key point: {e}")

    def _add_annotation(
        self,
        ax,
        ann: Dict,
        x_min: float,
        x_max: float,
        y_min: float,
        y_max: float,
        index: int = 0,
    ):
        """Add a text annotation, optionally with an arrow.

        The index parameter helps spread multiple annotations to avoid overlap.
        """
        try:
            x = x_min + (x_max - x_min) * ann.get("x_fraction", 0.5)
            y = y_min + (y_max - y_min) * ann.get("y_fraction", 0.5)
            text = ann.get("text", "")

            # Offset annotations vertically based on index to prevent overlap
            # Alternate between above and below the specified position
            y_offset = (index % 3) * 0.08 * (y_max - y_min)
            if index % 2 == 1:
                y_offset = -y_offset
            y = y + y_offset

            # Clamp y to stay within plot bounds
            y = max(y_min + 0.05 * (y_max - y_min), min(y, y_max - 0.05 * (y_max - y_min)))

            if ann.get("arrow_to_x") is not None and ann.get("arrow_to_y") is not None:
                ax_target = x_min + (x_max - x_min) * ann["arrow_to_x"]
                ay_target = y_min + (y_max - y_min) * ann["arrow_to_y"]
                ax.annotate(
                    text,
                    xy=(ax_target, ay_target),
                    xytext=(x, y),
                    fontsize=10,
                    fontweight="bold",
                    arrowprops=dict(arrowstyle="->", lw=1.5, color="gray"),
                    bbox=dict(
                        boxstyle="round,pad=0.3",
                        facecolor="white",
                        edgecolor="#888888",
                        alpha=0.95,
                    ),
                )
            else:
                ax.text(
                    x, y, text,
                    fontsize=10,
                    bbox=dict(
                        boxstyle="round,pad=0.3",
                        facecolor="white",
                        edgecolor="#888888",
                        alpha=0.9,
                    ),
                )
        except Exception as e:
            logger.debug(f"Could not add annotation: {e}")

    # ==================================================================
    # Utilities
    # ==================================================================
    def _clean_json(self, text: str) -> str:
        """Strip markdown code fences from LLM JSON output."""
        cleaned = text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        return cleaned.strip()

    def _fig_to_base64(self, fig) -> str:
        """Convert matplotlib figure to base64 string."""
        buffer = io.BytesIO()
        # Use the fixed figsize (10x7) without bbox_inches="tight" to
        # prevent annotations/legends from stretching the figure to
        # extreme dimensions when tight_layout fails.
        fig.savefig(buffer, format="png", dpi=150, pad_inches=0.3)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close(fig)
        return image_base64


# Global instance
universal_graph_generator = UniversalGraphGenerator()
