from sentence_transformers import SentenceTransformer
import asyncio
from typing import List

model = SentenceTransformer("all-mpnet-base-v2")

async def get_embedding(text: str) -> List[float]:
    """Async wrapper for embedding generation"""
    try:
        # Run synchronous model.encode in a thread
        result = await asyncio.to_thread(
            model.encode,
            text,
            convert_to_numpy=True,
            normalize_embeddings=True
        )
        return result.tolist()  # Convert numpy array to list
    except Exception as e:
        raise RuntimeError(f"Embedding generation failed: {str(e)}")