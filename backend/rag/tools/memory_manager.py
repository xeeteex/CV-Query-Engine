import os
import uuid
import logging
from datetime import datetime
from typing import List, Dict, Optional
from pymongo import MongoClient
from langchain.llms.base import LLM

logger = logging.getLogger(__name__)

# MongoDB setup
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["cv_database"]
collection = db["rag_memory"]

def summarize_for_memory(query: str, response: str, llm: LLM) -> str:
    """Use LLM to summarize user/system interaction."""
    prompt = f"""
    Summarize this interaction in 2-3 sentences for memory recall.

    USER QUESTION:
    {query}

    SYSTEM RESPONSE:
    {response}

    SUMMARY:
    """
    result = llm.invoke(prompt)
    return result.content.strip() if hasattr(result, "content") else str(result).strip()

def save_memory(
    email: str,
    session_id: Optional[str],
    query: str,
    response: str,
    llm: LLM,
    user_context: Optional[Dict] = None,
):
    """
    Save memory with summarization.

    Args:
        email (str): User email
        session_id (str): Session ID (generated if missing)
        query (str): User query
        response (str): Full system response
        llm (LLM): LangChain LLM instance for summarization
        user_context (dict): Optional metadata like IP, user-agent
    """
    if not email or not isinstance(email, str):
        raise ValueError("A valid email is required to store memory.")

    email = email.strip().lower()
    session_id = session_id if session_id and isinstance(session_id, str) else str(uuid.uuid4())
    summary = summarize_for_memory(query, response, llm)

    memory_doc = {
        "email": email,
        "session_id": session_id,
        "query": query,
        "response_summary": summary,
        "full_response": response,
        "timestamp": datetime.utcnow(),
        "source": "chat",
        "user_context": user_context or {}
    }

    try:
        collection.insert_one(memory_doc)
        logger.info(f"[Memory] Stored for {email} | Session: {session_id}")
    except Exception as e:
        logger.error(f"[Memory] Error saving memory: {e}", exc_info=True)

def load_recent_memory(
    email: str,
    session_id: Optional[str] = None,
    limit: int = 3
) -> List[Dict[str, str]]:
    """
    Retrieve memory entries for a user/session.

    Args:
        email (str): Required user email
        session_id (str): Optional session filter
        limit (int): Max entries to retrieve

    Returns:
        List of memory dicts with query + summary
    """
    if not email or not isinstance(email, str):
        logger.warning("[Memory] Invalid email provided")
        return []

    query = {"email": email.strip().lower()}
    if session_id and isinstance(session_id, str):
        query["session_id"] = session_id

    try:
        docs = collection.find(query).sort("timestamp", -1).limit(limit)
        return [
            {
                "query": d.get("query", ""),
                "response": d.get("response_summary", d.get("full_response", "")),
                "timestamp": d.get("timestamp", datetime.utcnow()).isoformat(),
                "session_id": d.get("session_id", "")
            }
            for d in docs
        ]
    except Exception as e:
        logger.error(f"[Memory] Retrieval error: {e}", exc_info=True)
        return []
