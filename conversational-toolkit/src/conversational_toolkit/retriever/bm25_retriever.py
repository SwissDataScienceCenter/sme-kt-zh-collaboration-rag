"""
BM25 lexical retriever backed by 'rank-bm25'.

'rank-bm25' provides a well-tested BM25 Okapi implementation and several
variants (BM25L, BM25Plus). The corpus is tokenised and indexed at construction
time; retrieval is a pure in-memory operation with no I/O cost per query.

Typical usage: initialise from a list of 'ChunkRecord' objects already stored
in a vector store, then combine with a 'VectorStoreRetriever' inside a
'HybridRetriever' for lexical + semantic search.
"""

import re

from rank_bm25 import BM25Okapi  # type: ignore[import-untyped]

from conversational_toolkit.retriever.base import Retriever
from conversational_toolkit.vectorstores.base import ChunkMatch, ChunkRecord


class BM25Retriever(Retriever[ChunkMatch]):
    """
    In-memory BM25 retriever over a fixed corpus of 'ChunkRecord' objects.

    Uses 'rank_bm25.BM25Okapi' under the hood. The corpus is tokenised with a simple word-boundary regex (lowercased) at construction time.

    Attributes:
        corpus: The indexed document chunks.
    """

    def __init__(self, corpus: list[ChunkRecord], top_k: int) -> None:
        super().__init__(top_k)
        self.corpus = corpus
        tokenized = [self._tokenize(chunk.content) for chunk in corpus]
        self._bm25 = BM25Okapi(tokenized)

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """Lowercase word-boundary tokenisation."""
        return re.findall(r"\b\w+\b", text.lower())

    async def retrieve(self, query: str) -> list[ChunkMatch]:
        """Score the corpus against 'query' using BM25 and return the top 'top_k' matches."""
        query_terms = self._tokenize(query)
        scores: list[float] = self._bm25.get_scores(query_terms).tolist()
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[: self.top_k]
        return [
            ChunkMatch(
                id=self.corpus[i].id,
                title=self.corpus[i].title,
                content=self.corpus[i].content,
                mime_type=self.corpus[i].mime_type,
                metadata=self.corpus[i].metadata,
                embedding=self.corpus[i].embedding,
                score=scores[i],
            )
            for i in top_indices
        ]
