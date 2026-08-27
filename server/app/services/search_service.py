import logging
from typing import List, Dict, Tuple, Optional, Any
from app.config import settings
from app.models.chunk import CodeChunk, SearchResultItem, SearchResponse
from app.services.bm25_service import bm25_service
from app.services.jina_service import jina_service
from app.services.qdrant_service import qdrant_service

logger = logging.getLogger(__name__)


class SearchService:
    def __init__(self):
        # Store active repository chunk registries in memory: repo_id -> Dict[chunk_id, CodeChunk]
        self._repo_chunks: Dict[str, Dict[str, CodeChunk]] = {}
        # Track indexed content_hashes per repo to support incremental indexing: repo_id -> Dict[chunk_id, content_hash]
        self._repo_indexed_hashes: Dict[str, Dict[str, str]] = {}

    def index_repository_chunks(
        self,
        repository_id: str,
        new_chunks: List[CodeChunk],
    ) -> Dict[str, Any]:
        """
        Indexes chunks using Incremental Indexing:
        1. Compares new chunks against previously indexed hashes.
        2. Identifies:
           - Unchanged chunks (skipped, 0 Jina tokens)
           - New/Modified chunks (embedded via Jina & upserted to Qdrant)
           - Stale/Deleted chunks (removed from Qdrant)
        3. Updates BM25 index and in-memory registry.
        """
        if not new_chunks:
            return {
                "total_chunks": 0,
                "new_or_modified": 0,
                "unchanged": 0,
                "deleted": 0,
                "status": "empty_repository",
            }

        prev_hashes = self._repo_indexed_hashes.get(repository_id, {})
        new_chunks_map = {c.chunk_id: c for c in new_chunks}

        chunks_to_embed: List[CodeChunk] = []
        chunks_to_embed_tuples: List[Tuple[str, str]] = []
        unchanged_count = 0

        for chunk in new_chunks:
            prev_hash = prev_hashes.get(chunk.chunk_id)
            if prev_hash == chunk.content_hash and jina_service.is_cached(chunk.content_hash):
                unchanged_count += 1
            else:
                chunks_to_embed.append(chunk)
                # Formulate text representation for semantic code embedding
                # Including file path, class/function signature, and code gives rich semantic signals
                embed_text = (
                    f"File: {chunk.file_path}\n"
                    f"Language: {chunk.language}\n"
                    f"Class: {chunk.class_name or 'N/A'}\n"
                    f"Function: {chunk.function_name or 'N/A'}\n\n"
                    f"{chunk.code}"
                )
                chunks_to_embed_tuples.append((embed_text, chunk.content_hash))

        # Deleted chunks: in prev_hashes but not in new_chunks_map
        deleted_chunk_ids = [cid for cid in prev_hashes if cid not in new_chunks_map]

        logger.info(
            f"Indexing repo '{repository_id}': total={len(new_chunks)}, "
            f"new/modified={len(chunks_to_embed)}, unchanged={unchanged_count}, "
            f"deleted={len(deleted_chunk_ids)}"
        )

        # Generate embeddings & upsert to Qdrant only for new/modified chunks
        if chunks_to_embed:
            vectors = jina_service.embed_code_chunks(chunks_to_embed_tuples)
            qdrant_service.upsert_chunks(repository_id, chunks_to_embed, vectors)

        # Cleanup deleted chunks from Qdrant
        if deleted_chunk_ids:
            qdrant_service.delete_chunks(repository_id, deleted_chunk_ids)

        # Update BM25 index (built from all current active chunks)
        bm25_service.index_repository(repository_id, new_chunks)

        # Update in-memory registries
        self._repo_chunks[repository_id] = new_chunks_map
        self._repo_indexed_hashes[repository_id] = {c.chunk_id: c.content_hash for c in new_chunks}

        return {
            "total_chunks": len(new_chunks),
            "new_or_modified": len(chunks_to_embed),
            "unchanged": unchanged_count,
            "deleted": len(deleted_chunk_ids),
            "status": "indexed",
        }

    def hybrid_search(
        self,
        repository_id: str,
        query: str,
        top_k: int = 10,
    ) -> SearchResponse:
        """
        Executes Hybrid Search combining BM25 keyword matching + Jina/Qdrant Semantic Search.
        Deduplicates results by chunk_id and computes normalized weighted score:
        final_score = BM25_WEIGHT * norm_bm25_score + SEMANTIC_WEIGHT * norm_semantic_score
        """
        clean_query = query.strip()
        if not clean_query:
            return SearchResponse(
                query=query,
                repository_id=repository_id,
                total_results=0,
                results=[],
            )

        bm25_weight = settings.BM25_WEIGHT
        semantic_weight = settings.SEMANTIC_WEIGHT
        total_weight = bm25_weight + semantic_weight
        if total_weight > 0:
            bm25_weight = bm25_weight / total_weight
            semantic_weight = semantic_weight / total_weight

        # 1. BM25 Search
        bm25_results = bm25_service.search(repository_id, clean_query, top_k=top_k * 2)

        # 2. Semantic Search (Jina + Qdrant)
        semantic_results: List[Dict[str, Any]] = []
        try:
            query_vector = jina_service.embed_query(clean_query)
            semantic_results = qdrant_service.search(repository_id, query_vector, top_k=top_k * 2)
        except Exception as e:
            logger.warning(f"Semantic search failed, falling back to BM25 only: {str(e)}")

        # 3. Merge and Deduplicate Results by chunk_id
        # chunk_id -> {"chunk": ..., "bm25_score": float, "semantic_score": float, "type": str}
        merged: Dict[str, Dict[str, Any]] = {}

        for chunk, b_score in bm25_results:
            merged[chunk.chunk_id] = {
                "chunk_id": chunk.chunk_id,
                "file_path": chunk.file_path,
                "class_name": chunk.class_name,
                "function_name": chunk.function_name,
                "language": chunk.language,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                "code": chunk.code,
                "bm25_score": b_score,
                "semantic_score": 0.0,
                "has_bm25": True,
                "has_semantic": False,
            }

        for sem in semantic_results:
            cid = sem["chunk_id"]
            s_score = sem["score"]
            if cid in merged:
                merged[cid]["semantic_score"] = s_score
                merged[cid]["has_semantic"] = True
            else:
                merged[cid] = {
                    "chunk_id": cid,
                    "file_path": sem["file_path"],
                    "class_name": sem["class_name"],
                    "function_name": sem["function_name"],
                    "language": sem.get("language", ""),
                    "start_line": sem["start_line"],
                    "end_line": sem["end_line"],
                    "code": sem["code"],
                    "bm25_score": 0.0,
                    "semantic_score": s_score,
                    "has_bm25": False,
                    "has_semantic": True,
                }

        # 4. Compute Final Weighted Score and Search Type Tag
        ranked_items: List[SearchResultItem] = []
        for item in merged.values():
            final_score = (
                bm25_weight * item["bm25_score"] + semantic_weight * item["semantic_score"]
            )

            if item["has_bm25"] and item["has_semantic"]:
                stype = "hybrid"
            elif item["has_semantic"]:
                stype = "semantic"
            else:
                stype = "bm25"

            ranked_items.append(
                SearchResultItem(
                    chunk_id=item["chunk_id"],
                    file_path=item["file_path"],
                    class_name=item["class_name"],
                    function_name=item["function_name"],
                    code=item["code"],
                    language=item["language"],
                    start_line=item["start_line"],
                    end_line=item["end_line"],
                    score=round(final_score, 4),
                    search_type=stype,
                )
            )

        # 5. Sort Descending by Final Score and slice top_k
        ranked_items.sort(key=lambda x: x.score, reverse=True)
        final_results = ranked_items[:top_k]

        return SearchResponse(
            query=clean_query,
            repository_id=repository_id,
            total_results=len(final_results),
            results=final_results,
        )


search_service = SearchService()
