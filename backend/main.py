from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from api.endpoints.upload import router as upload_router
from config.settings import settings
import uvicorn
from pinecone import Pinecone, ServerlessSpec

# Initialize FastAPI app
app = FastAPI(title="CV Search Engine API")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload_router, prefix="/api/v1/cvs", tags=["CV Upload"])

@app.on_event("startup")
async def startup():
    """Initialize services at startup"""
    # Initialize Pinecone client
    pc = Pinecone(api_key=settings.PINECONE_API_KEY)
    
    # Create index if doesn't exist
    if settings.PINECONE_INDEX_NAME not in pc.list_indexes().names():
        pc.create_index(
            name=settings.PINECONE_INDEX_NAME,
            dimension=768,
            spec=ServerlessSpec(  # Add proper spec
                cloud='aws',
                region='us-east-1'
            ),
            metadata_config={
                "indexed": [
                    "name", "skills", "role", 
                    "education", "file_hash"  # Remove "certifications" if not in metadata
                ]
            }
        )

@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    # No explicit cleanup needed with the new Pinecone client

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        workers=3
    )