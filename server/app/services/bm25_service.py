import re
import math
from typing import List, Tuple, Dict, Optional
from rank_bm25 import BM25Plus
from app.models.chunk import CodeChunk


class BM25Service:
    def __init__(self):
        # Cache BM25 models and chunk mappings keyed by repository_id
        # repo_id -> {"model": BM25Plus, "chunks": List[CodeChunk]}
        self._indices: Dict[str, Dict] = {}

    @staticmethod
    def tokenize(text: str) -> List[str]:
        """
        Tokenize code and natural language text for BM25.
        Splits on non-alphanumeric characters, splits camelCase and snake_case.
        """
        if not text:
            return []

        # 1. Lowercase raw text
        # 2. Split camelCase tokens e.g. getUserById -> get User By Id
        camel_split = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)
        
        # 3. Extract alphanumeric tokens
        tokens = re.findall(r"[A-Za-z0-9_]+", camel_split.lower())
        
        # 4. Split snake_case sub-tokens
        sub_tokens = []
        for t in tokens:
            parts = t.split("_")
            for p in parts:
                if len(p) > 1:  # ignore single char noise
                    sub_tokens.append(p)
            if len(t) > 1 and "_" in t:
                sub_tokens.append(t.replace("_", ""))

        return sub_tokens

    def index_repository(self, repository_id: str, chunks: List[CodeChunk]) -> None:
        """
        Builds or updates the BM25 index for a given repository.
        """
        if not chunks:
            self._indices.pop(repository_id, None)
            return

        corpus = []
        for c in chunks:
            # Combine searchable attributes: file_name, class_name, function_name, code
            doc_text = f"{c.file_path} {c.class_name or ''} {c.function_name or ''} {c.code}"
            tokens = self.tokenize(doc_text)
            corpus.append(tokens if tokens else ["empty"])

        bm25 = BM25Plus(corpus)
        self._indices[repository_id] = {
            "model": bm25,
            "chunks": chunks,
        }

    def search(
        self, repository_id: str, query: str, top_k: int = 10
    ) -> List[Tuple[CodeChunk, float]]:
        """
        Executes BM25 keyword search over indexed repository chunks.
        Returns List of (CodeChunk, normalized_bm25_score).
        """
        if not query.strip() or repository_id not in self._indices:
            return []

        index_data = self._indices[repository_id]
        bm25: BM25Okapi = index_data["model"]
        chunks: List[CodeChunk] = index_data["chunks"]

        query_tokens = self.tokenize(query)
        if not query_tokens:
            return []

        scores = bm25.get_scores(query_tokens)
        
        # Filter non-zero scores and pair with chunks
        ranked = []
        max_score = 0.0
        for i, score in enumerate(scores):
            if score > 0.0:
                ranked.append((chunks[i], float(score)))
                if score > max_score:
                    max_score = float(score)

        if not ranked:
            return []

        # Sort descending by score
        ranked.sort(key=lambda x: x[1], reverse=True)
        top_results = ranked[:top_k]

        # Normalize BM25 scores to [0.0, 1.0] range
        normalized_results = []
        for chunk, score in top_results:
            norm_score = score / max_score if max_score > 0 else 0.0
            normalized_results.append((chunk, norm_score))

        return normalized_results

    def is_indexed(self, repository_id: str) -> bool:
        return repository_id in self._indices


bm25_service = BM25Service()
