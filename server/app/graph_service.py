import os
import io
import base64
import json
import logging
from typing import Dict, List, Tuple, Optional, Any
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from sympy import symbols, lambdify, sympify
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

class GraphGenerator:
    def __init__(self):
        self.model = ChatOpenAI(model_name="gpt-4o", temperature=0.1)
    
    async def generate_ppf_curve(self, good1: str = "Guns", good2: str = "Butter", 
                                points: Optional[List[Tuple[float, float]]] = None) -> str:
        """Generate Production Possibilities Frontier curve"""
        
        # Check cache first
        parameters = {"good1": good1, "good2": good2, "points": points}
        cached_image = await graph_storage.get_cached_graph("ppf", parameters)
        if cached_image:
            return cached_image
        
        if not points:
            # Use AI to generate realistic PPF data points
            points = await self._get_ppf_data_points(good1, good2)
            parameters["points"] = points
        
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Extract x and y coordinates
        x_coords = [p[0] for p in points]
        y_coords = [p[1] for p in points]
        
        # Create smooth curve
        x_smooth = np.linspace(0, max(x_coords), 100)
        # Fit a simple concave curve (typical for PPF)
        y_smooth = max(y_coords) * (1 - (x_smooth / max(x_coords)) ** 1.5)
        
        # Plot PPF curve
        ax.plot(x_smooth, y_smooth, 'b-', linewidth=3, label='PPF Curve')
        ax.fill_between(x_smooth, 0, y_smooth, alpha=0.2, color='lightblue', label='Attainable Region')
        
        # Plot example points
        ax.scatter(x_coords, y_coords, color='red', s=100, zorder=5)
        
        # Add point labels
        for i, (x, y) in enumerate(points):
            ax.annotate(f'Point {chr(65+i)}', (x, y), xytext=(5, 5), 
                       textcoords='offset points', fontsize=10)
        
        # Formatting
        ax.set_xlabel(f'{good1} (units)', fontsize=12)
        ax.set_ylabel(f'{good2} (units)', fontsize=12)
        ax.set_title(f'Production Possibilities Frontier: {good1} vs {good2}', fontsize=14, pad=20)
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_xlim(0, max(x_coords) * 1.1)
        ax.set_ylim(0, max(y_coords) * 1.1)
        
        image_base64 = self._fig_to_base64(fig)
        
        # Store in cache
        await graph_storage.store_graph("ppf", parameters, image_base64, 
                                       tags=["unit1", "ppf", "trade-offs"])
        
        return image_base64
    
    async def generate_ppf_shift(self, good1: str = "Guns", good2: str = "Butter") -> str:
        """Generate PPF curve showing an outward shift due to technology/resources"""
        
        # Check cache first
        parameters = {"good1": good1, "good2": good2, "type": "shift"}
        cached_image = await graph_storage.get_cached_graph("ppf_shift", parameters)
        if cached_image:
            return cached_image
        
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Generate original PPF points
        original_points = await self._get_ppf_data_points(good1, good2)
        
        # Generate shifted PPF points (increased by 30-50%)
        shift_factor = 1.4
        shifted_points = [(x * shift_factor, y * shift_factor) for x, y in original_points]
        
        # Create smooth curves for both PPFs
        def create_ppf_curve(points, color, label, alpha=0.7):
            x_coords = [p[0] for p in points]
            y_coords = [p[1] for p in points]
            x_smooth = np.linspace(0, max(x_coords), 100)
            y_smooth = max(y_coords) * (1 - (x_smooth / max(x_coords)) ** 1.5)
            ax.plot(x_smooth, y_smooth, color=color, linewidth=3, label=label, alpha=alpha)
            return x_smooth, y_smooth
        
        # Plot original PPF (dashed)
        create_ppf_curve(original_points, 'gray', 'Original PPF', alpha=0.5)
        
        # Plot shifted PPF (solid)
        x_new, y_new = create_ppf_curve(shifted_points, 'blue', 'New PPF (after technology improvement)')
        
        # Add arrow showing the shift
        mid_idx = len(x_new) // 2
        x_orig = x_new[mid_idx] / shift_factor
        y_orig = y_new[mid_idx] / shift_factor
        ax.annotate('', xy=(x_new[mid_idx], y_new[mid_idx]), xytext=(x_orig, y_orig),
                   arrowprops=dict(arrowstyle='->', lw=2, color='red'))
        ax.text((x_orig + x_new[mid_idx])/2, (y_orig + y_new[mid_idx])/2 + max(y_new)*0.05, 
               'Economic Growth\n(Technology/Resources)', 
               ha='center', va='bottom', fontsize=10, color='red', weight='bold')
        
        # Formatting
        ax.set_xlabel(f'{good1} (units)', fontsize=12)
        ax.set_ylabel(f'{good2} (units)', fontsize=12)
        ax.set_title(f'PPF Shift: Impact of Economic Growth\n{good1} vs {good2}', fontsize=14, pad=20)
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Set limits based on shifted PPF
        max_x = max([p[0] for p in shifted_points]) * 1.1
        max_y = max([p[1] for p in shifted_points]) * 1.1
        ax.set_xlim(0, max_x)
        ax.set_ylim(0, max_y)
        
        image_base64 = self._fig_to_base64(fig)
        
        # Store in cache
        await graph_storage.store_graph("ppf_shift", parameters, image_base64, 
                                       tags=["unit1", "ppf", "economic-growth", "technology"])
        
        return image_base64
    
    async def generate_supply_demand_curve(self, market: str = "Generic Market",
                                         equilibrium_price: float = 10,
                                         equilibrium_quantity: float = 100) -> str:
        """Generate supply and demand curves"""
        
        # Check cache first
        parameters = {"market": market, "equilibrium_price": equilibrium_price, 
                     "equilibrium_quantity": equilibrium_quantity}
        cached_image = await graph_storage.get_cached_graph("supply_demand", parameters)
        if cached_image:
            return cached_image
        
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Generate quantity range
        q = np.linspace(0, equilibrium_quantity * 2, 100)
        
        # Supply curve: upward sloping
        supply_price = equilibrium_price * (q / equilibrium_quantity) ** 0.5
        
        # Demand curve: downward sloping  
        demand_price = equilibrium_price * 2 - (equilibrium_price * q / equilibrium_quantity)
        demand_price = np.maximum(demand_price, 0)  # Price can't be negative
        
        # Plot curves
        ax.plot(q, supply_price, 'r-', linewidth=3, label='Supply')
        ax.plot(q, demand_price, 'b-', linewidth=3, label='Demand')
        
        # Mark equilibrium point
        ax.plot(equilibrium_quantity, equilibrium_price, 'go', markersize=12, 
                label=f'Equilibrium (Q={equilibrium_quantity}, P=${equilibrium_price})')
        
        # Add equilibrium lines
        ax.axhline(y=equilibrium_price, color='gray', linestyle='--', alpha=0.7)
        ax.axvline(x=equilibrium_quantity, color='gray', linestyle='--', alpha=0.7)
        
        # Formatting
        ax.set_xlabel('Quantity', fontsize=12)
        ax.set_ylabel('Price ($)', fontsize=12)
        ax.set_title(f'Supply and Demand: {market}', fontsize=14, pad=20)
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_xlim(0, equilibrium_quantity * 2)
        ax.set_ylim(0, equilibrium_price * 2.2)
        
        image_base64 = self._fig_to_base64(fig)
        
        # Store in cache
        await graph_storage.store_graph("supply_demand", parameters, image_base64,
                                       tags=["supply", "demand", "equilibrium"])
        
        return image_base64
    
    async def generate_elasticity_graph(self, demand_type: str = "elastic") -> str:
        """Generate price elasticity of demand visualization"""
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        q = np.linspace(1, 100, 100)
        
        if demand_type.lower() == "elastic":
            # Elastic demand - flat curve
            p1 = 50 - 0.3 * q
            p1 = np.maximum(p1, 0)
            title1 = "Elastic Demand (Ed > 1)"
            
            # Inelastic demand - steep curve
            p2 = 50 - 0.05 * q
            p2 = np.maximum(p2, 0)
            title2 = "Inelastic Demand (Ed < 1)"
        else:
            # Inelastic demand - steep curve
            p1 = 50 - 0.05 * q
            p1 = np.maximum(p1, 0)
            title1 = "Inelastic Demand (Ed < 1)"
            
            # Elastic demand - flat curve
            p2 = 50 - 0.3 * q
            p2 = np.maximum(p2, 0)
            title2 = "Elastic Demand (Ed > 1)"
        
        # Plot both curves
        ax1.plot(q, p1, 'b-', linewidth=3)
        ax1.set_title(title1, fontsize=12)
        ax1.set_xlabel('Quantity')
        ax1.set_ylabel('Price')
        ax1.grid(True, alpha=0.3)
        
        ax2.plot(q, p2, 'r-', linewidth=3)
        ax2.set_title(title2, fontsize=12)
        ax2.set_xlabel('Quantity')
        ax2.set_ylabel('Price')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return self._fig_to_base64(fig)
    
    async def generate_custom_economic_graph(self, graph_request: str) -> str:
        """Generate custom economic graphs based on AI-parsed parameters"""
        
        # Use AI to parse the graph request and extract parameters
        graph_params = await self._parse_graph_request(graph_request)
        
        if graph_params["type"] == "ppf":
            return await self.generate_ppf_curve(
                graph_params.get("good1", "Good X"),
                graph_params.get("good2", "Good Y"),
                graph_params.get("points")
            )
        elif graph_params["type"] == "supply_demand":
            return await self.generate_supply_demand_curve(
                graph_params.get("market", "Market"),
                graph_params.get("equilibrium_price", 10),
                graph_params.get("equilibrium_quantity", 100)
            )
        elif graph_params["type"] == "elasticity":
            return await self.generate_elasticity_graph(
                graph_params.get("demand_type", "elastic")
            )
        else:
            # Default to supply and demand
            return await self.generate_supply_demand_curve()
    
    async def _get_ppf_data_points(self, good1: str, good2: str) -> List[Tuple[float, float]]:
        """Use AI to generate realistic PPF data points"""
        
        prompt = ChatPromptTemplate.from_template("""
        Generate 5 realistic data points for a Production Possibilities Frontier (PPF) curve 
        between {good1} and {good2}. 
        
        Return ONLY a JSON array of [x, y] coordinate pairs where:
        - x represents units of {good1}
        - y represents units of {good2}
        - Points should show the trade-off between the two goods
        - Points should be realistic for these goods
        - Include corner points (maximum of each good)
        
        Example format: [[0, 100], [25, 80], [50, 60], [75, 35], [100, 0]]
        """)
        
        chain = prompt | self.model | StrOutputParser()
        response = await chain.ainvoke({"good1": good1, "good2": good2})
        
        try:
            points = json.loads(response.strip())
            return [(float(p[0]), float(p[1])) for p in points]
        except:
            # Fallback points
            return [(0, 100), (25, 80), (50, 60), (75, 35), (100, 0)]
    
    async def _parse_graph_request(self, request: str) -> Dict[str, Any]:
        """Parse natural language graph request into parameters"""
        
        prompt = ChatPromptTemplate.from_template("""
        Parse this graph request and return parameters as JSON:
        "{request}"
        
        Determine the graph type and extract relevant parameters:
        
        Types: "ppf", "supply_demand", "elasticity"
        
        Return JSON format:
        {{
            "type": "graph_type",
            "good1": "first good name",
            "good2": "second good name", 
            "market": "market name",
            "equilibrium_price": number,
            "equilibrium_quantity": number,
            "demand_type": "elastic" or "inelastic"
        }}
        
        Only include relevant parameters for the detected graph type.
        """)
        
        chain = prompt | self.model | StrOutputParser()
        response = await chain.ainvoke({"request": request})
        
        try:
            return json.loads(response.strip())
        except:
            return {"type": "supply_demand"}
    
    def _fig_to_base64(self, fig) -> str:
        """Convert matplotlib figure to base64 string"""
        buffer = io.BytesIO()
        fig.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close(fig)  # Free memory
        return image_base64

# Global instance
graph_generator = GraphGenerator()