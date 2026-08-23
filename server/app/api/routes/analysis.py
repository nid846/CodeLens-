from fastapi import APIRouter, HTTPException, status
from app.models.analysis import AnalysisRequest, AnalysisResult
from app.services.repository_analyzer import RepositoryAnalyzer
from app.services.github_service import GitHubServiceError

router = APIRouter()


@router.get("/health")
def health_check():
    return {"status": "ok", "service": "CodeLens API", "version": "1.0.0"}


@router.post("/analyze", response_model=AnalysisResult)
def analyze_repository(request: AnalysisRequest):
    if not request.github_url or not request.github_url.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GitHub URL cannot be empty.",
        )

    try:
        result = RepositoryAnalyzer.analyze_repository(request.github_url)
        return result
    except GitHubServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during repository analysis: {str(e)}",
        )
