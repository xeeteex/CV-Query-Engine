from rag.utils.flatten import extract_metadata_from_cv, validate_and_fill_metadata
from rag.chunker import chunk_text
from rag.pinecone_client import store_chunks
from rag.utils.flatten import flatten_metadata
import json

def index_cv(cv_text: str, doc_id: str):
    chunks = chunk_text(cv_text)
    metadata = extract_metadata_from_cv(cv_text)
    
    # DEBUG: Print raw extraction
    print(f"Raw extracted metadata:\n{json.dumps(metadata, indent=2)}")
    
    validated = validate_and_fill_metadata(cv_text, metadata)
    flattened = flatten_metadata(validated, cv_text)
    
    # Ensure we keep all data
    flattened["RAW_EXTRACTION_JSON"] = json.dumps(metadata)
    
    # DEBUG: Print final flattened
    print(f"Final flattened metadata:\n{json.dumps(flattened, indent=2)}")
    
    metadatas = [flattened for _ in chunks]
    store_chunks(chunks, doc_id, metadatas)