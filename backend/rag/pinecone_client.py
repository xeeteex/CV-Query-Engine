import os
import asyncio
from pinecone import Pinecone
from rag.embedder import model  # your sentence-transformer model

# Load env variables
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")

# Check if environment variables are set
if not PINECONE_API_KEY:
    print("ERROR: PINECONE_API_KEY environment variable not set")
    print("Please create a .env file in the backend directory with:")
    print("PINECONE_API_KEY=your_pinecone_api_key_here")
    print("PINECONE_INDEX_NAME=your_pinecone_index_name_here")
    raise ValueError("PINECONE_API_KEY environment variable not set")

if not PINECONE_INDEX_NAME:
    print("ERROR: PINECONE_INDEX_NAME environment variable not set")
    print("Please create a .env file in the backend directory with:")
    print("PINECONE_API_KEY=your_pinecone_api_key_here")
    print("PINECONE_INDEX_NAME=your_pinecone_index_name_here")
    raise ValueError("PINECONE_INDEX_NAME environment variable not set")

# Initialize Pinecone client
pc = Pinecone(api_key=PINECONE_API_KEY)

# Connect to index
index = pc.Index(PINECONE_INDEX_NAME)

def store_chunks(chunks, doc_id, metadatas=None):
    """
    Upsert dense vectors and rich metadata for each chunk.
    chunks: list of text chunks
    doc_id: unique document ID
    metadatas: list of metadata dicts (one per chunk), each may include name, location, skills, experience, etc.
    """
    vectors = model.encode(chunks).tolist()
    to_upsert = []
    for i in range(len(chunks)):
        meta = {
            "text": chunks[i],
            "doc_id": doc_id
        }
        # If extra metadata is provided, merge it in
        if metadatas and i < len(metadatas):
            meta.update(metadatas[i])
        to_upsert.append({
            "id": f"{doc_id}-{i}",
            "values": vectors[i],
            "metadata": meta
        })
    print("Upserting the following payload:", to_upsert)
    index.upsert(vectors=to_upsert)

def query_chunks(query, filters=None, top_k=5):
    try:
        print(f"Querying Pinecone for: {query}")
        
        # Embed the query
        vector = model.encode([query])[0].tolist()

        # Query Pinecone index with optional metadata filters
        result = index.query(
            vector=vector,
            filter=filters or {},
            top_k=top_k,

            include_metadata=True,
        )

        # Build rich result objects with metadata and score
        chunks = []
        for match in result["matches"]:
            meta = match.get("metadata", {}) or {}
            chunks.append({
                "id": match.get("id"),
                "score": match.get("score", 0.0),
                "metadata": meta,
                "text": meta.get("text", "")
            })
        print(f"Found {len(chunks)} chunks from Pinecone")
        return chunks
        
    except Exception as e:
        print(f"Error querying Pinecone: {str(e)}")
        return []
