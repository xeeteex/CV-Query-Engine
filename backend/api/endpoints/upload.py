from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from core.pipelines.upload import UploadPipeline
from services.embeddings import get_embedding
from services.pinecone_ops import upsert_cv
import logging
from typing import Optional

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/upload")
async def upload_cv(file: UploadFile = File(...)):
    """Endpoint that handles the full CV processing pipeline"""
    try:
        # 1. Basic validation
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")

        # 2. Read file content
        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(status_code=400, detail="Empty file")

        # 3. Process through pipeline
        pipeline = UploadPipeline()
        processed_data: Optional[dict] = await pipeline.process(file_bytes, file.filename)
        
        if not processed_data:
            raise HTTPException(status_code=409, detail="Duplicate CV detected")

        # 4. Generate embeddings and store
        embedding = await get_embedding(processed_data["embedding_input"])
        await upsert_cv(
            cv_id=processed_data["id"],
            embedding=embedding,
            metadata=processed_data["metadata"],
            namespace=processed_data["namespace"]
        )

        # 5. Return success response
        return JSONResponse({
            "status": "success",
            "cv_id": processed_data["id"],
            "role": processed_data["metadata"].get("role"),
            "namespace": processed_data["namespace"]
        })

    except HTTPException:
        raise  # Re-raise existing HTTP exceptions
    except Exception as e:
        logger.error(f"Upload processing failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"CV processing failed: {str(e)}"
        )