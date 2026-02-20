import os
from typing import List, Dict, Any, Optional
from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue

class QdrantRepository:
    """Repository pattern abstraction for Qdrant Vector Database."""
    
    def __init__(self, collection_name: str, vector_size: int = 768):
        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        qdrant_api_key = os.getenv("QDRANT_API_KEY")
        self.client = AsyncQdrantClient(url=qdrant_url, api_key=qdrant_api_key)
        self.collection_name = collection_name
        self.vector_size = vector_size

    async def ensure_collection(self):
        """Creates the collection if it does not exist."""
        collections = await self.client.get_collections()
        exists = any(c.name == self.collection_name for c in collections.collections)
        
        if not exists:
            await self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE)
            )

    async def upsert_vector(self, point_id: str, vector: List[float], payload: Dict[str, Any]):
        """Upsert a single vector with metadata payload."""
        point = PointStruct(id=point_id, vector=vector, payload=payload)
        await self.client.upsert(
            collection_name=self.collection_name,
            points=[point]
        )

    async def search_hybrid(self, query_vector: List[float], filter_map: Optional[Dict[str, Any]] = None, limit: int = 5) -> List[Dict[str, Any]]:
        """Perform a vector search with optional strong metadata filtering."""
        
        qdrant_filter = None
        if filter_map:
            conditions = [
                FieldCondition(key=k, match=MatchValue(value=v))
                for k, v in filter_map.items()
            ]
            qdrant_filter = Filter(must=conditions)
            
        results = await self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            query_filter=qdrant_filter,
            limit=limit
        )
        
        return [
            {
                "id": hit.id,
                "score": hit.score,
                "payload": hit.payload
            }
            for hit in results
        ]
