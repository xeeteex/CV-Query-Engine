# Simple in-memory conversation memory for sessions/users
# In production, replace with persistent storage (e.g., Redis, DB)

import threading

# Thread-safe memory store
_memory_store = {}
_memory_lock = threading.Lock()


def add_message(session_id: str, role: str, message: str):
    """Add a message to the memory for a session."""
    with _memory_lock:
        if session_id not in _memory_store:
            _memory_store[session_id] = []
        _memory_store[session_id].append({"role": role, "message": message})


def get_memory(session_id: str):
    """Get the full memory for a session."""
    with _memory_lock:
        return list(_memory_store.get(session_id, []))


def compress_memory(memory: list, max_messages: int = 10):
    """Compress memory to the last N messages (simple strategy)."""
    return memory[-max_messages:] if len(memory) > max_messages else memory 