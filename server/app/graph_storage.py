import os
import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv(override=True)

class GraphStorage:
    def __init__(self):
        self.client = None
        self.db = None
        self.collection = None
        self._connect()
    
    def _connect(self):
        """Initialize MongoDB connection"""
        mongodb_uri = os.getenv("MONGODB_URI")
        if mongodb_uri:
            try:
                self.client = MongoClient(mongodb_uri, server_api=ServerApi("1"))
                self.db = self.client.Academis
                self.collection = self.db.graphs
                logger.info("Graph storage connected to MongoDB")
            except Exception as e:
                logger.error(f"Failed to connect to MongoDB: {e}")
    
    def _generate_graph_id(self, graph_type: str, parameters: Dict[str, Any]) -> str:
        """Generate unique ID based on graph type and parameters"""
        # Create deterministic hash from parameters
        param_str = json.dumps(parameters, sort_keys=True)
        param_hash = hashlib.md5(param_str.encode()).hexdigest()[:8]
        return f"{graph_type}_{param_hash}"
    
    async def get_cached_graph(self, graph_type: str, parameters: Dict[str, Any]) -> Optional[str]:
        """Retrieve cached graph if it exists and hasn't expired"""
        if self.collection is None:
            return None
        
        graph_id = self._generate_graph_id(graph_type, parameters)
        
        try:
            # Find non-expired graph
            cached_graph = self.collection.find_one({
                "graph_id": graph_id,
                "expires_at": {"$gt": datetime.utcnow()}
            })
            
            if cached_graph:
                logger.info(f"Retrieved cached graph: {graph_id}")
                return cached_graph["image_base64"]
            
        except Exception as e:
            logger.error(f"Error retrieving cached graph: {e}")
        
        return None
    
    async def store_graph(self, graph_type: str, parameters: Dict[str, Any], 
                         image_base64: str, subject: str = "economics",
                         tags: List[str] = None, ttl_days: int = 30) -> str:
        """Store graph in MongoDB with metadata"""
        if self.collection is None:
            logger.warning("MongoDB not available - skipping graph storage")
            return ""
        
        graph_id = self._generate_graph_id(graph_type, parameters)
        
        # Calculate image metadata
        image_size = len(image_base64) * 3 // 4  # Approximate bytes from base64
        
        graph_doc = {
            "graph_id": graph_id,
            "type": graph_type,
            "subject": subject,
            "parameters": parameters,
            "image_base64": image_base64,
            "metadata": {
                "title": self._generate_title(graph_type, parameters),
                "created_at": datetime.utcnow(),
                "file_size": image_size,
                "dimensions": "1000x800"  # Default from matplotlib figsize
            },
            "tags": tags or [],
            "expires_at": datetime.utcnow() + timedelta(days=ttl_days)
        }
        
        try:
            # Upsert (insert or update)
            result = self.collection.replace_one(
                {"graph_id": graph_id},
                graph_doc,
                upsert=True
            )
            
            if result.upserted_id:
                logger.info(f"Stored new graph: {graph_id}")
            else:
                logger.info(f"Updated existing graph: {graph_id}")
            
            return graph_id
            
        except Exception as e:
            logger.error(f"Error storing graph: {e}")
            return ""
    
    def _generate_title(self, graph_type: str, parameters: Dict[str, Any]) -> str:
        """Generate human-readable title from graph parameters"""
        if graph_type == "ppf":
            good1 = parameters.get("good1", "Good X")
            good2 = parameters.get("good2", "Good Y")
            return f"Production Possibilities Frontier: {good1} vs {good2}"
        
        elif graph_type == "supply_demand":
            market = parameters.get("market", "Market")
            return f"Supply and Demand: {market}"
        
        elif graph_type == "elasticity":
            demand_type = parameters.get("demand_type", "elastic")
            return f"Price Elasticity of Demand ({demand_type.title()})"
        
        else:
            return f"{graph_type.title()} Graph"
    
    async def get_graph_by_id(self, graph_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve graph by ID"""
        if self.collection is None:
            return None
        
        try:
            graph = self.collection.find_one({"graph_id": graph_id})
            if graph:
                # Remove MongoDB ObjectId for JSON serialization
                graph.pop("_id", None)
                return graph
        except Exception as e:
            logger.error(f"Error retrieving graph by ID: {e}")
        
        return None
    
    async def list_graphs(self, subject: str = None, graph_type: str = None, 
                         limit: int = 50) -> List[Dict[str, Any]]:
        """List stored graphs with optional filtering"""
        if self.collection is None:
            return []
        
        try:
            # Build query
            query = {"expires_at": {"$gt": datetime.utcnow()}}
            if subject:
                query["subject"] = subject
            if graph_type:
                query["type"] = graph_type
            
            # Get graphs (exclude large image data in listing)
            cursor = self.collection.find(
                query,
                {"image_base64": 0}  # Exclude base64 data from listing
            ).sort("metadata.created_at", -1).limit(limit)
            
            graphs = []
            for graph in cursor:
                graph.pop("_id", None)  # Remove ObjectId
                graphs.append(graph)
            
            return graphs
            
        except Exception as e:
            logger.error(f"Error listing graphs: {e}")
            return []
    
    async def cleanup_expired_graphs(self) -> int:
        """Remove expired graphs and return count deleted"""
        if self.collection is None:
            return 0
        
        try:
            result = self.collection.delete_many({
                "expires_at": {"$lt": datetime.utcnow()}
            })
            
            if result.deleted_count > 0:
                logger.info(f"Cleaned up {result.deleted_count} expired graphs")
            
            return result.deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired graphs: {e}")
            return 0

# Global instance
graph_storage = GraphStorage()