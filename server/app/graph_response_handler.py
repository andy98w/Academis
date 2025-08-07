import re
import logging
from typing import Dict, Any, Optional, Tuple
from .graph_service import graph_generator

logger = logging.getLogger(__name__)

class GraphResponseHandler:
    """Handle graph suggestions in RAG responses based on keyword detection"""
    
    @staticmethod
    def extract_graph_suggestion(response: str) -> Tuple[str, bool, Optional[str]]:
        """
        Check if response contains [GRAPH] or [GRAPH:description] tag
        Returns: (cleaned_response, should_generate_graph, graph_description)
        """
        import re
        
        # Check for [GRAPH:description] format
        graph_match = re.search(r'\[GRAPH:([^\]]+)\]', response)
        if graph_match:
            description = graph_match.group(1)
            cleaned_response = re.sub(r'\[GRAPH:[^\]]+\]', '', response).strip()
            return cleaned_response, True, description
        
        # Check for simple [GRAPH] format
        if '[GRAPH]' in response:
            cleaned_response = response.replace('[GRAPH]', '').strip()
            return cleaned_response, True, None
        
        return response, False, None
    
    @staticmethod
    async def generate_contextual_graph(response_text: str, question: str) -> Optional[Dict[str, Any]]:
        """
        Generate appropriate graph based on context from response and question
        Returns: graph data dict or None
        """
        try:
            # Combine response and question for context analysis
            full_context = f"{response_text} {question}".lower()
            
            # Determine graph type based on keywords in context
            if GraphResponseHandler._is_ppf_context(full_context):
                return await GraphResponseHandler._generate_ppf_from_context(full_context)
            elif GraphResponseHandler._is_supply_demand_context(full_context):
                return await GraphResponseHandler._generate_supply_demand_from_context(full_context)
            elif GraphResponseHandler._is_elasticity_context(full_context):
                return await GraphResponseHandler._generate_elasticity_from_context(full_context)
            else:
                # Default to PPF for general economic concepts
                return await GraphResponseHandler._generate_ppf_from_context(full_context)
                
        except Exception as e:
            logger.error(f"Error generating contextual graph: {e}")
            return None
    
    @staticmethod
    def _is_ppf_context(text: str) -> bool:
        """Check if context suggests PPF graph"""
        ppf_keywords = [
            "production possibilities", "ppf", "trade-off", "opportunity cost",
            "scarcity", "efficient", "inefficient", "attainable", "unattainable",
            "resource allocation", "production frontier", "maximum production"
        ]
        return any(keyword in text for keyword in ppf_keywords)
    
    @staticmethod
    def _is_supply_demand_context(text: str) -> bool:
        """Check if context suggests supply and demand graph"""
        sd_keywords = [
            "supply and demand", "equilibrium", "market price", "quantity demanded",
            "quantity supplied", "demand curve", "supply curve", "market clearing",
            "shortage", "surplus", "price mechanism"
        ]
        return any(keyword in text for keyword in sd_keywords)
    
    @staticmethod
    def _is_elasticity_context(text: str) -> bool:
        """Check if context suggests elasticity graph"""
        elasticity_keywords = [
            "elasticity", "elastic", "inelastic", "price sensitive", 
            "responsiveness", "percentage change", "steep curve", "flat curve"
        ]
        return any(keyword in text for keyword in elasticity_keywords)
    
    @staticmethod
    async def _generate_ppf_from_context(context: str) -> Dict[str, Any]:
        """Generate economic graph from context"""
        
        # Use custom graph generator that can interpret the context
        image_base64 = await graph_generator.generate_custom_economic_graph(context)
        
        return {
            "type": "custom",
            "image": image_base64,
            "title": "Economic Graph",
            "description": "This graph illustrates the economic concepts discussed in the text."
        }
    
    @staticmethod
    async def _generate_supply_demand_from_context(context: str) -> Dict[str, Any]:
        """Generate supply and demand graph from context"""
        
        # Extract market from context if possible  
        market = GraphResponseHandler._extract_market_from_text(context)
        
        image_base64 = await graph_generator.generate_supply_demand_curve(market)
        
        return {
            "type": "supply_demand", 
            "image": image_base64,
            "title": f"Supply and Demand: {market}",
            "description": "This graph shows how supply and demand curves intersect to determine equilibrium price and quantity."
        }
    
    @staticmethod
    async def _generate_elasticity_from_context(context: str) -> Dict[str, Any]:
        """Generate elasticity graph from context"""
        
        # Determine if elastic or inelastic from context
        demand_type = "elastic" if "elastic" in context else "inelastic" if "inelastic" in context else "elastic"
        
        image_base64 = await graph_generator.generate_elasticity_graph(demand_type)
        
        return {
            "type": "elasticity",
            "image": image_base64, 
            "title": f"Price Elasticity of Demand ({demand_type.title()})",
            "description": f"This graph illustrates {demand_type} demand, showing how quantity responds to price changes."
        }
    
    @staticmethod
    def _extract_goods_from_text(text: str) -> Tuple[str, str]:
        """Extract two goods from text for PPF graph"""
        
        # Common economics examples
        economics_pairs = [
            ("guns", "butter"), ("cars", "computers"), ("wheat", "steel"),
            ("capital goods", "consumer goods"), ("military", "civilian"),
            ("pizza", "cola"), ("food", "clothing")
        ]
        
        # Look for common pairs first
        for good1, good2 in economics_pairs:
            if good1 in text and good2 in text:
                return good1.title(), good2.title()
        
        # Look for individual goods mentioned
        common_goods = ["cars", "computers", "wheat", "steel", "guns", "butter", 
                       "food", "clothing", "pizza", "cola", "books", "movies"]
        
        found_goods = [good for good in common_goods if good in text]
        
        if len(found_goods) >= 2:
            return found_goods[0].title(), found_goods[1].title()
        elif len(found_goods) == 1:
            return found_goods[0].title(), "Other Goods"
        
        # Default fallback
        return "Good X", "Good Y"
    
    @staticmethod
    def _extract_market_from_text(text: str) -> str:
        """Extract market name from text"""
        
        # Common market examples
        markets = ["coffee", "housing", "labor", "oil", "gas", "food", "car", "book"]
        
        for market in markets:
            if market in text:
                return f"{market.title()} Market"
        
        return "Generic Market"

# Global instance
graph_response_handler = GraphResponseHandler()