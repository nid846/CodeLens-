import uuid
import hashlib
from typing import List, Optional
from pydantic import BaseModel, Field

# Deterministic namespace for CodeLens chunk UUIDs
CODELENS_NAMESPACE = uuid.UUID("a3b4c5d6-e7f8-40a1-b2c3-d4e5f6a7b8c9")


class CodeChunk(BaseModel):
    chunk_id: str = Field(..., description="Deterministic unique identifier for the chunk (valid UUID)")
    repository_id: str = Field(..., description="Repository identifier (e.g. owner/repo)")
    file_path: str = Field(..., description="Relative path of the source file")
    file_name: str = Field(..., description="Name of the file")
    language: str = Field(..., description="Programming language of the chunk")
    class_name: Optional[str] = Field(None, description="Name of containing class")
    function_name: Optional[str] = Field(None, description="Name of function/method")
    code: str = Field(..., description="Extracted code snippet content")
    start_line: int = Field(..., description="Starting line number in file (1-indexed)")
    end_line: int = Field(..., description="Ending line number in file (1-indexed)")
    imports: List[str] = Field(default_factory=list, description="Related imports")
    dependencies: List[str] = Field(default_factory=list, description="Resolved target dependencies")
    content_hash: str = Field(..., description="SHA-256 hash of normalized code content")

    @staticmethod
    def compute_content_hash(code: str) -> str:
        """Compute deterministic SHA-256 hash of code content."""
        normalized = "\n".join(line.rstrip() for line in code.strip().splitlines())
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    @staticmethod
    def generate_chunk_id(repository_id: str, file_path: str, start_line: int, end_line: int, name: str = "") -> str:
        """Generate deterministic valid UUIDv5 chunk identifier required by Qdrant."""
        raw_key = f"{repository_id}:{file_path}:{start_line}:{end_line}:{name}"
        return str(uuid.uuid5(CODELENS_NAMESPACE, raw_key))


class SearchRequest(BaseModel):
    repository_id: str = Field(..., description="Repository identifier to search within")
    query: str = Field(..., description="Natural language search query")
    top_k: int = Field(default=10, ge=1, le=50, description="Number of results to return")


class SearchResultItem(BaseModel):
    chunk_id: str
    file_path: str
    class_name: Optional[str] = None
    function_name: Optional[str] = None
    code: str
    language: str = ""
    start_line: int
    end_line: int
    score: float
    search_type: str = "hybrid"  # "hybrid" | "bm25" | "semantic"


class SearchResponse(BaseModel):
    query: str
    repository_id: str
    total_results: int
    results: List[SearchResultItem]
