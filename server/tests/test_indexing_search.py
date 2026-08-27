import pytest
from unittest.mock import patch, MagicMock
from app.models.analysis import (
    AnalysisResult,
    RepositoryInfo,
    AnalysisSummary,
    FileInfo,
    ClassInfo,
    FunctionInfo,
    DependencyInfo,
)
from app.models.chunk import CodeChunk
from app.services.chunking_service import ChunkingService
from app.services.bm25_service import BM25Service
from app.services.jina_service import JinaEmbeddingService, JinaTokenBudgetExceededError
from app.services.qdrant_service import QdrantService
from app.services.search_service import SearchService


# ==========================================
# 1. Chunking Tests
# ==========================================
def test_chunking_service_extraction():
    analysis = AnalysisResult(
        repository=RepositoryInfo(name="test_repo", url="https://github.com/org/test_repo"),
        summary=AnalysisSummary(total_files=1, total_classes=1, total_functions=2),
        files=[FileInfo(path="src/auth.py", name="auth.py", language="Python", size=500)],
        classes=[ClassInfo(name="AuthService", file_path="src/auth.py", start_line=4, end_line=15)],
        functions=[
            FunctionInfo(name="login", file_path="src/auth.py", containing_class="AuthService", start_line=5, end_line=9),
            FunctionInfo(name="logout", file_path="src/auth.py", containing_class="AuthService", start_line=10, end_line=14),
        ],
        dependencies=[DependencyInfo(source_file="src/auth.py", target_file="src/db.py", import_statement="import db")],
    )

    file_contents = {
        "src/auth.py": """# Header
import os
import db

class AuthService:
    def login(self, username, password):
        if not username:
            return False
        return True

    def logout(self, user_id):
        session.clear(user_id)
        return True
"""
    }

    chunks = ChunkingService.extract_chunks_from_analysis(analysis, file_contents, "org/test_repo")
    assert len(chunks) == 2
    assert chunks[0].function_name == "login"
    assert chunks[0].class_name == "AuthService"
    assert chunks[0].content_hash != ""
    assert "def login" in chunks[0].code
    assert chunks[1].function_name == "logout"
    assert chunks[1].dependencies == ["src/db.py"]


def test_chunking_service_fallback_file():
    analysis = AnalysisResult(
        repository=RepositoryInfo(name="doc_repo", url="https://github.com/org/doc_repo"),
        summary=AnalysisSummary(total_files=1),
        files=[FileInfo(path="schema.sql", name="schema.sql", language="SQL", size=200)],
    )
    file_contents = {"schema.sql": "CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(100));"}
    chunks = ChunkingService.extract_chunks_from_analysis(analysis, file_contents, "org/doc_repo")
    assert len(chunks) == 1
    assert chunks[0].file_path == "schema.sql"
    assert "CREATE TABLE" in chunks[0].code


# ==========================================
# 2. BM25 Tests
# ==========================================
def test_bm25_service_search_and_score():
    bm25 = BM25Service()
    c1 = CodeChunk(
        chunk_id="c1",
        repository_id="repo1",
        file_path="auth.py",
        file_name="auth.py",
        language="Python",
        function_name="authenticate_user",
        code="def authenticate_user(token):\n    verify_jwt(token)",
        start_line=1,
        end_line=2,
        content_hash="hash1",
    )
    c2 = CodeChunk(
        chunk_id="c2",
        repository_id="repo1",
        file_path="payment.py",
        file_name="payment.py",
        language="Python",
        function_name="process_payment",
        code="def process_payment(amount, card):\n    stripe_charge(amount)",
        start_line=1,
        end_line=2,
        content_hash="hash2",
    )

    bm25.index_repository("repo1", [c1, c2])
    
    # Search relevant keyword
    results = bm25.search("repo1", "authenticate token", top_k=5)
    assert len(results) >= 1
    top_chunk, score = results[0]
    assert top_chunk.chunk_id == "c1"
    assert 0.0 <= score <= 1.0

    # Search irrelevant keyword
    results_empty = bm25.search("repo1", "completely_unrelated_xyz", top_k=5)
    assert len(results_empty) == 0

    # Empty query
    assert len(bm25.search("repo1", "", top_k=5)) == 0


# ==========================================
# 3. Jina Embedding Tests (Mocked)
# ==========================================
def test_jina_deduplication_and_batching():
    jina = JinaEmbeddingService()
    mock_vector = [0.1] * 1024

    with patch.object(jina, "_call_jina_api", return_value=([mock_vector, mock_vector], 50)) as mock_api:
        chunks = [
            ("code snippet 1", "hash_abc"),
            ("code snippet 2", "hash_def"),
        ]
        vectors = jina.embed_code_chunks(chunks)
        assert len(vectors) == 2
        assert mock_api.call_count == 1

        # Second call with identical content hashes must use cache and NOT call API
        vectors_cached = jina.embed_code_chunks(chunks)
        assert len(vectors_cached) == 2
        assert mock_api.call_count == 1  # Still 1, 0 new network calls


def test_jina_token_budget_soft_cap():
    jina = JinaEmbeddingService()
    jina._total_tokens_used = 1000

    with patch("app.config.settings.JINA_MONTHLY_TOKEN_BUDGET", 1050):
        # 100 tokens requested when only 50 tokens remain before cap
        with pytest.raises(JinaTokenBudgetExceededError):
            jina.check_token_budget(100)


# ==========================================
# 4. Qdrant Isolation & Search Tests (Mocked)
# ==========================================
def test_qdrant_isolation_and_search():
    qdrant = QdrantService()
    mock_point = MagicMock()
    mock_point.id = "chunk_123"
    mock_point.score = 0.88
    mock_point.payload = {
        "chunk_id": "chunk_123",
        "file_path": "controllers/auth.py",
        "class_name": "AuthCtrl",
        "function_name": "login",
        "code": "def login(): pass",
        "start_line": 10,
        "end_line": 15,
    }

    mock_client = MagicMock()
    mock_coll = MagicMock()
    mock_coll.name = "codelens_code_chunks"
    mock_client.get_collections.return_value.collections = [mock_coll]
    if hasattr(mock_client, "query_points"):
        mock_response = MagicMock()
        mock_response.points = [mock_point]
        mock_client.query_points.return_value = mock_response
    else:
        mock_client.search.return_value = [mock_point]

    with patch.object(qdrant, "get_client", return_value=mock_client):
        results = qdrant.search("org/repo", [0.1] * 1024, top_k=5)
        assert len(results) == 1
        assert results[0]["chunk_id"] == "chunk_123"
        assert results[0]["score"] == 0.88


# ==========================================
# 5. Hybrid Search Tests
# ==========================================
def test_hybrid_search_deduplication_and_ranking():
    search_srv = SearchService()
    repo_id = "test/hybrid_repo"

    c1 = CodeChunk(
        chunk_id="c1",
        repository_id=repo_id,
        file_path="auth.py",
        file_name="auth.py",
        language="Python",
        function_name="login",
        code="def login(): pass",
        start_line=1,
        end_line=5,
        content_hash="h1",
    )

    # Mock BM25 results
    with patch("app.services.search_service.bm25_service.search", return_value=[(c1, 0.9)]):
        # Mock Semantic results with same chunk (hybrid overlap)
        with patch("app.services.search_service.jina_service.embed_query", return_value=[0.1] * 1024):
            with patch(
                "app.services.search_service.qdrant_service.search",
                return_value=[{
                    "chunk_id": "c1",
                    "file_path": "auth.py",
                    "class_name": None,
                    "function_name": "login",
                    "language": "Python",
                    "start_line": 1,
                    "end_line": 5,
                    "code": "def login(): pass",
                    "score": 0.8,
                }],
            ):
                response = search_srv.hybrid_search(repo_id, "login function", top_k=10)
                assert response.total_results == 1
                result_item = response.results[0]
                assert result_item.chunk_id == "c1"
                assert result_item.search_type == "hybrid"
                # (0.5 * 0.9) + (0.5 * 0.8) = 0.85
                assert abs(result_item.score - 0.85) < 0.01
