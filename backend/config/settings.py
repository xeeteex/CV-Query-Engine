from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Pinecone settings
    PINECONE_API_KEY: str
    PINECONE_INDEX_NAME: str = "api-cv-search"
    PINECONE_ENVIRONMENT: str = "us-east-1"
    
    # Embedding model
    EMBEDDING_MODEL: str = "all-mpnet-base-v2"
    
    # Mistral AI
    MISTRAL_API_KEY: str
    
    class Config:
        env_file = ".env"
        extra = "ignore"

# Create settings instance
settings = Settings()