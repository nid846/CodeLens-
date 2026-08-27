import os
from typing import Optional
from dotenv import load_dotenv

# Load server/.env if present
load_dotenv()


class Settings:
    # Jina Configuration
    JINA_API_KEY: str = os.getenv("JINA_API_KEY", "")
    JINA_EMBEDDING_MODEL: str = os.getenv("JINA_EMBEDDING_MODEL", "jina-embeddings-v3")
    JINA_EMBEDDING_DIMENSIONS: Optional[int] = (
        int(os.getenv("JINA_EMBEDDING_DIMENSIONS"))
        if os.getenv("JINA_EMBEDDING_DIMENSIONS")
        else 1024
    )
    JINA_MONTHLY_TOKEN_BUDGET: int = int(
        os.getenv("JINA_MONTHLY_TOKEN_BUDGET", "1000000")
    )

    # Qdrant Configuration
    QDRANT_URL: str = os.getenv("QDRANT_URL", "")
    QDRANT_API_KEY: str = os.getenv("QDRANT_API_KEY", "")
    QDRANT_COLLECTION_NAME: str = os.getenv("QDRANT_COLLECTION_NAME", "codelens_code_chunks")

    # Hybrid Search Weights
    BM25_WEIGHT: float = float(os.getenv("BM25_WEIGHT", "0.5"))
    SEMANTIC_WEIGHT: float = float(os.getenv("SEMANTIC_WEIGHT", "0.5"))


settings = Settings()
