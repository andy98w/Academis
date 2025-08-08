"""
Universal Graph Generation Service

This service analyzes any educational content and creates appropriate visualizations
without hardcoding specific graph types or economic concepts. It dynamically determines:
1. What variables/concepts need to be visualized
2. What type of relationship exists between them
3. How to best represent that relationship visually
"""

import os
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

load_dotenv()
logger = logging.getLogger(__name__)

# Set matplotlib to use non-interactive backend
plt.switch_backend('Agg')
sns.set_style("whitegrid")

class UniversalGraphGenerator:
    def __init__(self):
        self.model = ChatOpenAI(model_name="gpt-4o", temperature=0.2)
    
    async def generate_contextual_graph(self, content: str, context_title: str = "") -> Optional[Dict[str, Any]]:
        """
        Analyze content and generate an appropriate graph without assuming any specific domain
        """
        try:
            # Step 1: Analyze if visualization would help
            should_visualize = await self._analyze_visualization_need(content, context_title)
            
            if not should_visualize["needs_visualization"]:
                return None
            
            # Step 2: Extract the core relationship/concept to visualize
            visualization_spec = await self._extract_visualization_concept(content, context_title, should_visualize)
            
            if not visualization_spec:
                return None
                
            # Step 3: Generate the actual graph
            image_base64 = await self._create_universal_graph(visualization_spec)
            
            if not image_base64:
                return None
            
            # Cache the result
            await graph_storage.store_graph(
                visualization_spec.get("concept_type", "universal"), 
                visualization_spec.get("parameters", {}), 
                image_base64,
                tags=visualization_spec.get("tags", ["universal"])
            )
            
            return {
                "type": visualization_spec.get("concept_type", "relationship"),
                "image": image_base64,
                "title": visualization_spec.get("title", "Conceptual Visualization"),
                "description": visualization_spec.get("description", "Visual representation of the concepts discussed.")
            }
            
        except Exception as e:
            logger.error(f"Error in universal graph generation: {e}")
            return None
    
    async def _analyze_visualization_need(self, content: str, context_title: str) -> Dict[str, Any]:
        """Determine if the content would benefit from visualization"""
        
        prompt = ChatPromptTemplate.from_template("""
        Analyze this educational content to determine if it contains concepts that would benefit from visual representation.
        
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
            "reasoning": "explanation of why visualization would help"
        }}
        
        Be generous - if there are ANY relationships or concepts that could be clearer with a visual aid, suggest visualization.
        """)
        
        chain = prompt | self.model | StrOutputParser()
        response = await chain.ainvoke({
            "content": content[:2000],
            "context_title": context_title
        })
        
        try:
            return json.loads(response.strip())
        except:
            return {"needs_visualization": False, "reasoning": "Failed to parse analysis"}
    
    async def _extract_visualization_concept(self, content: str, context_title: str, analysis: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract what specifically should be visualized and how"""
        
        prompt = ChatPromptTemplate.from_template("""
        Based on this content and analysis, create a complete visualization specification.
        
        Content: {content}
        Title: {context_title}
        Analysis: {analysis}
        
        Create a visualization spec that captures the core relationship or concept. Return JSON:
        {{
            "concept_type": "descriptive name for what's being shown",
            "title": "clear title for the graph",
            "description": "what this visualization demonstrates",
            "x_variable": {{
                "name": "what goes on x-axis",
                "unit": "unit of measurement if any",
                "type": "continuous/discrete/categorical",
                "range_description": "how the variable changes"
            }},
            "y_variable": {{
                "name": "what goes on y-axis", 
                "unit": "unit of measurement if any",
                "type": "continuous/discrete/categorical",
                "range_description": "how the variable changes"
            }},
            "relationship": {{
                "type": "linear/curved/inverse/step/categorical/other",
                "direction": "positive/negative/mixed",
                "description": "describe the relationship in words"
            }},
            "key_points": [
                {{
                    "x_value": "description or approximate value",
                    "y_value": "description or approximate value", 
                    "significance": "why this point matters"
                }}
            ],
            "visual_elements": [
                {{
                    "type": "line/curve/area/point/arrow/text",
                    "purpose": "what it shows or emphasizes",
                    "style": "color/pattern suggestions"
                }}
            ],
            "parameters": {{}},
            "tags": ["relevant", "keywords"]
        }}
        
        Focus on the CORE relationship or concept, not specific domain knowledge.
        Make it educational and directly tied to what the content is teaching.
        """)
        
        chain = prompt | self.model | StrOutputParser()
        response = await chain.ainvoke({
            "content": content[:1500],
            "context_title": context_title,
            "analysis": json.dumps(analysis)
        })
        
        try:
            return json.loads(response.strip())
        except Exception as e:
            logger.error(f"Failed to parse visualization spec: {e}")
            return None
    
    async def _create_universal_graph(self, spec: Dict[str, Any]) -> Optional[str]:
        """Create a graph based on the universal specification"""
        
        try:
            fig, ax = plt.subplots(figsize=(10, 8))
            
            # Extract variables
            x_var = spec.get("x_variable", {})
            y_var = spec.get("y_variable", {})
            relationship = spec.get("relationship", {})
            
            # Generate data based on the relationship type
            data = await self._generate_universal_data(x_var, y_var, relationship, spec)
            
            # Plot the main relationship
            await self._plot_universal_relationship(ax, data, relationship, spec)
            
            # Add key points if specified
            await self._add_key_points(ax, spec.get("key_points", []), data)
            
            # Add visual elements
            await self._add_visual_elements(ax, spec.get("visual_elements", []), data)
            
            # Set labels and title
            x_label = x_var.get("name", "X Variable")
            y_label = y_var.get("name", "Y Variable")
            
            if x_var.get("unit"):
                x_label += f" ({x_var['unit']})"
            if y_var.get("unit"):
                y_label += f" ({y_var['unit']})"
            
            ax.set_xlabel(x_label, fontsize=12)
            ax.set_ylabel(y_label, fontsize=12)
            ax.set_title(spec.get("title", "Conceptual Relationship"), fontsize=14, pad=20)
            
            # Formatting
            ax.grid(True, alpha=0.3)
            
            return self._fig_to_base64(fig)
            
        except Exception as e:
            logger.error(f"Error creating universal graph: {e}")
            return None
    
    async def _generate_universal_data(self, x_var: Dict, y_var: Dict, relationship: Dict, spec: Dict) -> Dict[str, Any]:
        """Generate appropriate data based on variable types and relationships"""
        
        # Determine data range and type
        x_type = x_var.get("type", "continuous")
        y_type = y_var.get("type", "continuous") 
        rel_type = relationship.get("type", "linear")
        direction = relationship.get("direction", "positive")
        
        if x_type == "continuous" and y_type == "continuous":
            # Generate continuous data
            x = np.linspace(0, 100, 100)
            
            if rel_type == "linear":
                if direction == "positive":
                    y = 0.8 * x + np.random.normal(0, 5, len(x))
                elif direction == "negative":
                    y = 100 - 0.8 * x + np.random.normal(0, 5, len(x))
                else:  # mixed
                    y = 50 + 30 * np.sin(x / 20) + np.random.normal(0, 3, len(x))
            
            elif rel_type == "curved":
                if direction == "positive":
                    y = 100 * (1 - np.exp(-x / 30)) + np.random.normal(0, 3, len(x))
                elif direction == "negative":
                    y = 100 * np.exp(-x / 30) + np.random.normal(0, 3, len(x))
                else:
                    y = 50 + 40 * np.sin(x / 15) * np.exp(-x / 100) + np.random.normal(0, 2, len(x))
            
            elif rel_type == "inverse":
                y = 1000 / (x + 10) + np.random.normal(0, 2, len(x))
            
            else:  # other/step
                y = 50 + 20 * np.sign(np.sin(x / 15)) + np.random.normal(0, 3, len(x))
            
            # Ensure y values are reasonable
            y = np.maximum(y, 0)
            
        elif x_type == "categorical" or y_type == "categorical":
            # Generate categorical data
            categories = ["Category A", "Category B", "Category C", "Category D", "Category E"]
            if direction == "positive":
                values = [20, 35, 50, 65, 80]
            elif direction == "negative":
                values = [80, 65, 50, 35, 20]
            else:
                values = [30, 60, 45, 70, 40]
            
            return {"categories": categories, "values": values, "type": "categorical"}
        
        else:
            # Discrete data
            x = np.arange(0, 21)
            y = np.random.poisson(5, len(x)) + x * 0.5
        
        return {"x": x, "y": y, "type": "continuous"}
    
    async def _plot_universal_relationship(self, ax, data: Dict, relationship: Dict, spec: Dict):
        """Plot the main relationship"""
        
        if data.get("type") == "categorical":
            ax.bar(data["categories"], data["values"], alpha=0.7, color='steelblue')
        else:
            rel_type = relationship.get("type", "linear")
            
            if rel_type in ["linear", "inverse"]:
                ax.plot(data["x"], data["y"], 'b-', linewidth=2, alpha=0.8)
            elif rel_type == "curved":
                ax.plot(data["x"], data["y"], 'b-', linewidth=2, alpha=0.8)
                # Add curve fitting if needed
            else:
                ax.scatter(data["x"], data["y"], alpha=0.6, s=30, color='steelblue')
    
    async def _add_key_points(self, ax, key_points: List[Dict], data: Dict):
        """Add important points to highlight"""
        
        for point in key_points[:3]:  # Limit to 3 key points
            try:
                # For now, add points at approximate locations
                if data.get("type") == "continuous":
                    x_val = len(data["x"]) // 3  # Approximate position
                    y_val = data["y"][x_val]
                    ax.plot(data["x"][x_val], y_val, 'ro', markersize=8, zorder=5)
                    ax.annotate(point.get("significance", "Key Point")[:30] + "...", 
                               (data["x"][x_val], y_val), 
                               xytext=(10, 10), textcoords='offset points',
                               fontsize=9, ha='left',
                               bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7))
            except:
                continue
    
    async def _add_visual_elements(self, ax, elements: List[Dict], data: Dict):
        """Add additional visual elements like arrows, areas, etc."""
        
        for element in elements[:2]:  # Limit visual elements
            elem_type = element.get("type", "")
            purpose = element.get("purpose", "")
            
            if elem_type == "arrow" and data.get("type") == "continuous":
                # Add directional arrow
                mid_idx = len(data["x"]) // 2
                start_x, start_y = data["x"][mid_idx - 10], data["y"][mid_idx - 10]
                end_x, end_y = data["x"][mid_idx + 10], data["y"][mid_idx + 10]
                ax.annotate('', xy=(end_x, end_y), xytext=(start_x, start_y),
                           arrowprops=dict(arrowstyle='->', lw=2, color='red', alpha=0.7))
            
            elif elem_type == "area" and data.get("type") == "continuous":
                # Fill area under curve
                ax.fill_between(data["x"], 0, data["y"], alpha=0.2, color='lightblue')
            
            elif elem_type == "text":
                # Add explanatory text
                ax.text(0.02, 0.98, purpose[:50], transform=ax.transAxes, 
                       fontsize=10, verticalalignment='top',
                       bbox=dict(boxstyle="round,pad=0.4", facecolor="wheat", alpha=0.8))
    
    def _fig_to_base64(self, fig) -> str:
        """Convert matplotlib figure to base64 string"""
        buffer = io.BytesIO()
        fig.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close(fig)  # Free memory
        return image_base64

# Global instance
universal_graph_generator = UniversalGraphGenerator()