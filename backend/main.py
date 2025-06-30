import os, uuid, shutil
import logging
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile, File, Request, Body
from pymongo import MongoClient
from typing import Optional, Dict, Any
from auth.routes import router 
from typing import List, Dict, Any

# Configure logger
logger = logging.getLogger(__name__)
# Load environment variables first
load_dotenv()

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from rag.extractor import extract_pdf, extract_docx
from rag.chunker import chunk_text
from rag.pinecone_client import store_chunks, query_chunks, index  # Import index from pinecone_client
# from rag.agentic_rag import extract_structured_cv_data, filter_relevant_candidates, extract_basic_metadata_from_cv
from rag.index_cv import index_cv
from rag.pipeline import run_cv_query_pipeline
from langchain_mistralai import ChatMistralAI

# Initialize LLM for RAG pipeline
llm = ChatMistralAI(model="mistral-small-latest", temperature=0.1)

# Simple Pinecone client wrapper for the RAG pipeline
class PineconeClientWrapper:
    @staticmethod
    def query(vector, filters=None, top_k=5):
        return index.query(
            vector=vector,
            filter=filters,
            top_k=top_k,
            include_metadata=True
        )

pinecone_client = PineconeClientWrapper()

MONGODB_URI = "mongodb+srv://xeeteexstha:abcd1234@auth.exmhjp5.mongodb.net/cv_database?retryWrites=true&w=majority&appName=Auth"

# Initialize MongoDB client for memory
client = MongoClient(MONGODB_URI)
db = client["cv_database"]
memory_collection = db["rag_memory"]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_db_client():
    app.mongodb_client = MongoClient(MONGODB_URI)
    # Explicitly get the database from the client
    app.mongodb = app.mongodb_client.get_database("cv_database")

@app.on_event("shutdown")
def shutdown_db_client():
    app.mongodb_client.close()

app.include_router(router, prefix="/api/auth", tags=["auth"])

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    ext = file.filename.split('.')[-1].lower()
    path = f"temp/{uuid.uuid4()}.{ext}"

    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    if ext == "pdf":
        text = extract_pdf(path)
    elif ext == "docx":
        text = extract_docx(path)
    else:
        return {"error": "Unsupported file format"}

    index_cv(text, file.filename)

    return {"message": f"CV ingested from {file.filename}"}

def get_user_info(request: Request, payload: dict) -> Dict[str, Any]:
    """Extract user information from request and payload."""
    email = "anonymous@example.com"
    session_id = str(uuid.uuid4())
    user_context = {}
    
    # Try to get user from JWT token if available
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        try:
            token = auth_header.split(" ")[1]
            # In a real app, you would validate the JWT token here
            # For example: payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"]
            # email = payload.get("email", email)
            pass
        except Exception as e:
            logger.warning(f"Error processing auth token: {e}")
    
    # Override with payload values if provided
    if "email" in payload and isinstance(payload["email"], str):
        email = payload["email"].strip().lower()
    
    if "session_id" in payload and isinstance(payload["session_id"], str):
        session_id = payload["session_id"]
    
    # Add request metadata
    user_context.update({
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "request_id": str(uuid.uuid4())
    })
    
    return {
        "email": email,
        "session_id": session_id,
        "user_context": user_context
    }

@app.post("/ask/")
async def ask_question(
    request: Request,
    payload: dict = Body(...)
):
    """
    Process a user question and return a response using the RAG pipeline.
    
    Expected payload:
    {
        "question": "Your question here",
        "email": "user@example.com",  # Optional, defaults to anonymous
        "session_id": "session-id"    # Optional, auto-generated if not provided
    }
    """
    try:
        question = payload.get("question", "").strip()
        if not question:
            raise HTTPException(status_code=400, detail="Question is required")
        
        # Get user and session info
        user_info = get_user_info(request, payload)
        
        logger.info(f"Processing query for {user_info['email']} (session: {user_info['session_id']})")
        
        # Run the enhanced RAG pipeline with memory
        results = run_cv_query_pipeline(
            user_query=question,
            llm=llm,
            email=user_info["email"],
            session_id=user_info["session_id"],
            top_k=8,
            memory=memory_collection,
            user_context=user_info["user_context"]
        )
        # Ensure we have a plain dict
        if hasattr(results, 'dict'):
            results = results.dict()
        
        # Handle different response types
        if results.get("immediate_response"):
            return {
                "answer": results["immediate_response"],
                "sources": [],
                "structured_data": []
            }
            
        if not results.get("success", True):
            return {
                "answer": results.get("response", "Unable to process your query"),
                "error": results.get("error"),
                "sources": [],
                "structured_data": []
            }
        
        # Format successful response
        structured_data = results.get("candidates", [])
        answer = results.get("response", "")
        
        if not answer and structured_data:
            answer = format_structured_response(structured_data)
        
        response_data = {
            "answer": results.get("response", "No response generated"),
            "sources": results.get("sources", []),
            "structured_data": results.get("candidates", []),
            "session_id": user_info["session_id"],
            "request_id": user_info["user_context"].get("request_id")
        }
        
        if "debug" in payload:
            response_data["debug"] = {
                "user_email": user_info["email"],
                "session_id": user_info["session_id"]
            }
            
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query processing failed: {e}", exc_info=True)
        return {
            "answer": "An error occurred while processing your question",
            "error": str(e),
            "sources": [],
            "structured_data": []
        }

def format_structured_response(candidates: list) -> str:
    """Formats candidate data into readable text"""
    if not candidates:
        return "No matching candidates found"
    
    response = [f"Found {len(candidates)} matching candidates:"]
    
    for i, candidate in enumerate(candidates, 1):
        candidate_text = [
            f"{i}. {candidate.get('name', 'Unnamed Candidate')}",
            f"   Match Score: {candidate.get('match_score', 0)}%"
        ]
        
        if candidate.get('title'):
            candidate_text.append(f"   Current Role: {candidate['title']}")
        if candidate.get('skills'):
            candidate_text.append(f"   Top Skills: {', '.join(candidate['skills'][:5])}")
        if candidate.get('experience'):
            candidate_text.append(f"   Experience: {candidate['experience']} years")
            
        response.append("\n".join(candidate_text))
    
    return "\n\n".join(response)

# Comment out or remove these lines as they might be interfering with route registrations
# mcp = FastApiMCP(app)
# mcp.mount()