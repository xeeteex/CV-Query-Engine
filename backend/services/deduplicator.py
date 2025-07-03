import asyncio
import hashlib
from services.pinecone_ops import index

class Deduplicator:
    @staticmethod
    async def get_file_hash(file_bytes: bytes) -> str:
        # This is a CPU-bound operation, so we run it in a thread
        def _compute_hash():
            return hashlib.md5(file_bytes).hexdigest()
        return await asyncio.to_thread(_compute_hash)

    @staticmethod
    async def is_duplicate(file_hash: str) -> bool:
        # Pinecone query is synchronous, so we run it in a thread to keep it non-blocking
        def _query():
            result = index.query(
                vector=[0] * 768,  # Dummy vector since we're only filtering
                filter={"file_hash": {"$eq": file_hash}},
                top_k=1,
                include_metadata=True
            )
            return len(result.matches) > 0
            
        return await asyncio.to_thread(_query)