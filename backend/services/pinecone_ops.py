from pinecone import Pinecone
from config.settings import settings
from typing import List, Dict, Optional
import json
import logging

logger = logging.getLogger(__name__)

# Initialize Pinecone client
pc = Pinecone(api_key=settings.PINECONE_API_KEY)
index = pc.Index(settings.PINECONE_INDEX_NAME)

def _validate_metadata(metadata: Dict) -> Dict:
    """Ensure all metadata values are Pinecone-compatible"""
    validated = {}
    for key, value in metadata.items():
        if isinstance(value, (str, int, float, bool)):
            validated[key] = value
        elif isinstance(value, list):
            validated[key] = [str(item) for item in value]
        elif isinstance(value, dict):
            validated[key] = json.dumps(value)  # Convert dicts to JSON strings
        else:
            validated[key] = str(value)
    return validated

async def upsert_cv(
    cv_id: str,
    embedding: List[float],
    metadata: Dict,
    namespace: str
) -> bool:
    """Upsert CV data with validation and error handling"""
    try:
        validated_metadata = _validate_metadata(metadata)
        
        # Pinecone's Python client is synchronous, so no await needed
        index.upsert(
            vectors=[{
                "id": cv_id,
                "values": embedding,
                "metadata": validated_metadata
            }],
            namespace=namespace
        )
        return True
    except Exception as e:
        logger.error(f"Failed to upsert CV {cv_id}: {str(e)}")
        return False

async def search(
    query_embedding: List[float],
    namespace: Optional[str] = None,
    filter: Optional[Dict] = None,
    top_k: int = 10
) -> List[Dict]:
    """Search CVs with metadata parsing"""
    try:
        result = index.query(
            vector=query_embedding,
            namespace=namespace,
            filter=filter,
            top_k=top_k,
            include_metadata=True
        )
        
        parsed_results = []
        for match in result.matches:
            metadata = match.metadata
            # Parse JSON strings back to dicts
            if 'display_data' in metadata:
                try:
                    metadata['display_data'] = json.loads(metadata['display_data'])
                except json.JSONDecodeError:
                    pass
            parsed_results.append(metadata)
            
        return parsed_results
    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        return []