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

def store_chunks(chunks, doc_id):
    # Embed text chunks
    vectors = model.encode(chunks).tolist()

    # Prepare items for upsert
    to_upsert = [
        {
            "id": f"{doc_id}-{i}",
            "values": vectors[i],
            "metadata": {
                "text": chunks[i],
                "doc_id": doc_id,
            }
        }
        for i in range(len(chunks))
    ]

    # Upsert to Pinecone
    index.upsert(vectors=to_upsert)

def query_chunks(query, top_k=5):
    try:
        print(f"Querying Pinecone for: {query}")
        
        # Embed the query
        vector = model.encode([query])[0].tolist()

        # Query Pinecone index with timeout
        result = index.query(
            vector=vector,
            top_k=top_k,
            include_metadata=True,
        )

        # Return chunk texts from metadata
        chunks = [match["metadata"]["text"] for match in result["matches"]]
        print(f"Found {len(chunks)} chunks from Pinecone")
        return chunks
        
    except Exception as e:
        print(f"Error querying Pinecone: {str(e)}")
        return []
