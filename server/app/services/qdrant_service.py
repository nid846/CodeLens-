import logging
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from qdrant_client.http.exceptions import UnexpectedResponse
from app.config import settings
from app.models.chunk import CodeChunk

logger = logging.getLogger(__name__)


class QdrantServiceError(Exception):
    pass


class QdrantService:
    def __init__(self):
        self._client: Optional[QdrantClient] = None
        self._initialized = False

    def get_client(self) -> QdrantClient:
        if not settings.QDRANT_URL:
            raise QdrantServiceError("QDRANT_URL is not configured in .env file.")
        
        if self._client is None:
            try:
                self._client = QdrantClient(
                    url=settings.QDRANT_URL,
                    api_key=settings.QDRANT_API_KEY if settings.QDRANT_API_KEY else None,
                    timeout=30.0,
                )
            except Exception as e:
                raise QdrantServiceError(f"Failed to initialize Qdrant client: {str(e)}")
        return self._client

    def ensure_collection(self, vector_dim: int = 1024) -> None:
        """
        Ensure the collection exists in Qdrant with correct cosine similarity and vector dimension.
        Also creates payload index on repository_id for fast isolation filtering.
        """
        client = self.get_client()
        collection_name = settings.QDRANT_COLLECTION_NAME

        try:
            collections = client.get_collections().collections
            exists = any(c.name == collection_name for c in collections)

            if not exists:
                client.create_collection(
                    collection_name=collection_name,
                    vectors_config=qmodels.VectorParams(
                        size=vector_dim,
                        distance=qmodels.Distance.COSINE,
                    ),
                )
                logger.info(f"Created Qdrant collection '{collection_name}' with dim {vector_dim}")

            # Ensure repository_id keyword index exists for isolation filtering
            try:
                client.create_payload_index(
                    collection_name=collection_name,
                    field_name="repository_id",
                    field_schema=qmodels.PayloadSchemaType.KEYWORD,
                )
            except Exception:
                pass  # Index already exists

        except Exception as e:
            raise QdrantServiceError(f"Qdrant collection setup failed: {str(e)}")

    def upsert_chunks(
        self,
        repository_id: str,
        chunks: List[CodeChunk],
        vectors: List[List[float]],
    ) -> None:
        """
        Upsert chunk vectors and compact payload into Qdrant Cloud.
        Only essential metadata is stored in payload to respect free-tier capacity limits.
        """
        if not chunks or not vectors:
            return

        if len(chunks) != len(vectors):
            raise QdrantServiceError("Number of chunks does not match number of vectors.")

        client = self.get_client()
        collection_name = settings.QDRANT_COLLECTION_NAME

        # Ensure collection exists matching vector dimension
        vector_dim = len(vectors[0])
        self.ensure_collection(vector_dim)

        points = []
        for chunk, vector in zip(chunks, vectors):
            # Payload contains metadata necessary for identification and filtering (free-tier optimized)
            payload = {
                "chunk_id": chunk.chunk_id,
                "repository_id": repository_id,
                "file_path": chunk.file_path,
                "file_name": chunk.file_name,
                "language": chunk.language,
                "class_name": chunk.class_name,
                "function_name": chunk.function_name,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                "content_hash": chunk.content_hash,
                "code": chunk.code,  # stored for quick search result retrieval
            }

            points.append(
                qmodels.PointStruct(
                    id=chunk.chunk_id,
                    vector=vector,
                    payload=payload,
                )
            )

        # Batch upsert in chunks of 100
        batch_size = 100
        try:
            for i in range(0, len(points), batch_size):
                batch = points[i : i + batch_size]
                client.upsert(
                    collection_name=collection_name,
                    points=batch,
                )
        except Exception as e:
            raise QdrantServiceError(f"Failed to upsert points to Qdrant: {str(e)}")

    def search(
        self,
        repository_id: str,
        query_vector: List[float],
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Perform similarity search in Qdrant strictly filtered by repository_id for multi-tenant isolation.
        """
        client = self.get_client()
        collection_name = settings.QDRANT_COLLECTION_NAME

        filter_condition = qmodels.Filter(
            must=[
                qmodels.FieldCondition(
                    key="repository_id",
                    match=qmodels.MatchValue(value=repository_id),
                )
            ]
        )

        try:
            # Ensure collection exists before querying; if not created yet, return empty list gracefully
            collections = client.get_collections().collections
            if not any(c.name == collection_name for c in collections):
                logger.info(f"Qdrant collection '{collection_name}' does not exist yet. Returning empty semantic results.")
                return []

            # Check if query_points method exists or fallback to search
            if hasattr(client, "query_points"):
                search_response = client.query_points(
                    collection_name=collection_name,
                    query=query_vector,
                    query_filter=filter_condition,
                    limit=top_k,
                    with_payload=True,
                )
                points = search_response.points
            else:
                points = client.search(
                    collection_name=collection_name,
                    query_vector=query_vector,
                    query_filter=filter_condition,
                    limit=top_k,
                    with_payload=True,
                )

            results = []
            for pt in points:
                score = float(pt.score) if hasattr(pt, "score") else 0.0
                # Cosine distance in Qdrant produces scores in [-1.0, 1.0] or [0.0, 1.0]. Normalize to [0.0, 1.0]
                norm_score = max(0.0, min(1.0, (score + 1.0) / 2.0 if score < 0 else score))
                
                payload = pt.payload or {}
                results.append({
                    "chunk_id": payload.get("chunk_id", str(pt.id)),
                    "file_path": payload.get("file_path", ""),
                    "file_name": payload.get("file_name", ""),
                    "language": payload.get("language", ""),
                    "class_name": payload.get("class_name"),
                    "function_name": payload.get("function_name"),
                    "start_line": payload.get("start_line", 1),
                    "end_line": payload.get("end_line", 1),
                    "code": payload.get("code", ""),
                    "score": norm_score,
                })

            return results

        except Exception as e:
            if "doesn't exist" in str(e) or "Not found" in str(e):
                return []
            raise QdrantServiceError(f"Qdrant semantic search failed: {str(e)}")

    def delete_chunks(self, repository_id: str, chunk_ids: List[str]) -> None:
        """
        Delete specific chunks from Qdrant for incremental indexing cleanup.
        """
        if not chunk_ids:
            return
        client = self.get_client()
        collection_name = settings.QDRANT_COLLECTION_NAME
        try:
            client.delete(
                collection_name=collection_name,
                points_selector=qmodels.PointIdsList(points=chunk_ids),
            )
        except Exception as e:
            logger.warning(f"Failed to delete stale points from Qdrant: {str(e)}")


qdrant_service = QdrantService()
