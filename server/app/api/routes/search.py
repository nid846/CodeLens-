from fastapi import APIRouter, HTTPException, status
from app.models.chunk import SearchRequest, SearchResponse
from app.services.search_service import search_service

router = APIRouter()


@router.post("/search", response_model=SearchResponse)
def search_code(request: SearchRequest):
    """
    Search indexed code across repository using hybrid BM25 and semantic search.
    """
    if not request.query or not request.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query cannot be empty.",
        )

    if not request.repository_id or not request.repository_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Repository ID cannot be empty.",
        )

    try:
        results = search_service.hybrid_search(
            repository_id=request.repository_id.strip(),
            query=request.query.strip(),
            top_k=request.top_k,
        )
        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}",
        )
