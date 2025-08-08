import re
import logging
from typing import Dict, Any, Optional, Tuple
from .graph_service import universal_graph_generator

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
        Generate appropriate graph based on context using the dynamic graph generator
        Returns: graph data dict or None
        """
        try:
            # Combine response and question for context analysis
            full_context = f"{response_text} {question}"
            context_title = question[:100] if len(question) <= 100 else question[:100] + "..."
            
            # Use the universal graph generator - no hardcoded types
            return await universal_graph_generator.generate_contextual_graph(full_context, context_title)
                
        except Exception as e:
            logger.error(f"Error generating contextual graph: {e}")
            return None
    

# Global instance
graph_response_handler = GraphResponseHandler()