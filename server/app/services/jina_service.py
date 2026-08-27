import logging
from typing import List, Dict, Tuple, Optional
import httpx
from app.config import settings

logger = logging.getLogger(__name__)


class JinaServiceError(Exception):
    pass


class JinaTokenBudgetExceededError(JinaServiceError):
    pass


class JinaEmbeddingService:
    API_URL = "https://api.jina.ai/v1/embeddings"
    MAX_BATCH_SIZE = 64  # Maximum inputs per API call to respect payload limits

    def __init__(self):
        # In-memory vector cache keyed by content_hash to ensure we NEVER re-embed identical code chunks
        # content_hash -> List[float]
        self._vector_cache: Dict[str, List[float]] = {}
        
        # Approximate local cumulative token tracker
        self._total_tokens_used: int = 0

    @property
    def total_tokens_used(self) -> int:
        return self._total_tokens_used

    def reset_usage_tracker(self) -> None:
        self._total_tokens_used = 0

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """
        Lightweight fast token estimation (~4 chars per token for code/text).
        """
        if not text:
            return 0
        return max(1, len(text) // 4)

    def is_cached(self, content_hash: str) -> bool:
        return content_hash in self._vector_cache

    def get_cached_vector(self, content_hash: str) -> Optional[List[float]]:
        return self._vector_cache.get(content_hash)

    def cache_vector(self, content_hash: str, vector: List[float]) -> None:
        self._vector_cache[content_hash] = vector

    def check_token_budget(self, estimated_tokens: int) -> None:
        """
        Soft cap safeguard: Enforce monthly token budget before calling Jina API.
        """
        if settings.JINA_MONTHLY_TOKEN_BUDGET > 0:
            if (self._total_tokens_used + estimated_tokens) > settings.JINA_MONTHLY_TOKEN_BUDGET:
                raise JinaTokenBudgetExceededError(
                    f"Jina API token budget cap reached! Current usage: {self._total_tokens_used} tokens, "
                    f"estimated request: {estimated_tokens} tokens, "
                    f"configured limit: {settings.JINA_MONTHLY_TOKEN_BUDGET} tokens. "
                    f"Operation aborted to protect free tier allowance."
                )

    def _call_jina_api(
        self,
        texts: List[str],
        task: str = "retrieval.passage",
    ) -> Tuple[List[List[float]], int]:
        """
        Performs batched HTTP POST to Jina Embeddings API with token counting and error handling.
        """
        if not settings.JINA_API_KEY:
            raise JinaServiceError("JINA_API_KEY is not configured in .env file.")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.JINA_API_KEY}",
        }

        payload = {
            "model": settings.JINA_EMBEDDING_MODEL,
            "task": task,
            "input": texts,
        }

        if settings.JINA_EMBEDDING_DIMENSIONS:
            payload["dimensions"] = settings.JINA_EMBEDDING_DIMENSIONS

        try:
            with httpx.Client(timeout=45.0) as client:
                response = client.post(self.API_URL, json=payload, headers=headers)
                
                if response.status_code == 401 or response.status_code == 403:
                    raise JinaServiceError("Invalid or unauthorized Jina API Key.")
                elif response.status_code == 429:
                    raise JinaServiceError("Jina API rate limit exceeded. Please retry later.")
                elif response.status_code != 200:
                    raise JinaServiceError(f"Jina API returned error {response.status_code}: {response.text}")

                data = response.json()
                
                # Extract embeddings
                embeddings_data = data.get("data", [])
                embeddings = [item["embedding"] for item in embeddings_data]

                # Extract token usage from API response if present, otherwise approximate
                usage = data.get("usage", {})
                tokens_billed = usage.get("total_tokens", sum(self.estimate_tokens(t) for t in texts))

                return embeddings, tokens_billed

        except httpx.TimeoutException:
            raise JinaServiceError("Jina API request timed out after 45 seconds.")
        except httpx.RequestError as e:
            raise JinaServiceError(f"Network error connecting to Jina API: {str(e)}")

    def embed_code_chunks(
        self,
        chunks_content_and_hashes: List[Tuple[str, str]],
    ) -> List[List[float]]:
        """
        Embed code chunks using retrieval.passage adapter.
        Guarantees:
        1. Content-hash deduplication: skips chunks whose vectors are already cached.
        2. Aggressive batching (up to MAX_BATCH_SIZE).
        3. Token budget enforcement before making remote calls.
        """
        if not chunks_content_and_hashes:
            return []

        results: List[Optional[List[float]]] = [None] * len(chunks_content_and_hashes)
        uncached_indices: List[int] = []
        uncached_texts: List[str] = []

        # 1. Deduplication check via content_hash
        for i, (text, content_hash) in enumerate(chunks_content_and_hashes):
            if content_hash in self._vector_cache:
                results[i] = self._vector_cache[content_hash]
            else:
                uncached_indices.append(i)
                uncached_texts.append(text)

        if not uncached_texts:
            logger.info(f"All {len(chunks_content_and_hashes)} chunks found in cache. 0 Jina tokens consumed.")
            return [vec for vec in results if vec is not None]

        # 2. Estimate token cost & enforce budget
        total_estimated = sum(self.estimate_tokens(t) for t in uncached_texts)
        self.check_token_budget(total_estimated)

        # 3. Batch requests to Jina
        for batch_start in range(0, len(uncached_texts), self.MAX_BATCH_SIZE):
            batch_end = min(batch_start + self.MAX_BATCH_SIZE, len(uncached_texts))
            batch_texts = uncached_texts[batch_start:batch_end]
            batch_idxs = uncached_indices[batch_start:batch_end]

            vectors, tokens_used = self._call_jina_api(batch_texts, task="retrieval.passage")
            self._total_tokens_used += tokens_used

            for idx, text, vec in zip(batch_idxs, batch_texts, vectors):
                _, chash = chunks_content_and_hashes[idx]
                self.cache_vector(chash, vec)
                results[idx] = vec

        return [vec for vec in results if vec is not None]

    def embed_query(self, query: str) -> List[float]:
        """
        Embed a single search query using retrieval.query adapter.
        """
        if not query.strip():
            raise JinaServiceError("Query cannot be empty.")

        estimated = self.estimate_tokens(query)
        self.check_token_budget(estimated)

        vectors, tokens_used = self._call_jina_api([query], task="retrieval.query")
        self._total_tokens_used += tokens_used

        if not vectors:
            raise JinaServiceError("Failed to generate embedding for query.")
        return vectors[0]


jina_service = JinaEmbeddingService()
