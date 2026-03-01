"""
Hybrid retriever combining multiple retrievers via Reciprocal Rank Fusion.

'HybridRetriever' runs all sub-retrievers in parallel (using 'asyncio.gather') and merges their ranked result lists with RRF. RRF combines lexical search ('BM25Retriever') with semantic search ('VectorStoreRetriever') and is robust to score-scale differences between the two retrieval methods.

The RRF score assigned to each merged 'ChunkMatch' is the sum of 1 / (k + rank) contributions from each retriever that returned that chunk, where 'k' (default 60) dampens the influence of high ranks.
"""

import asyncio
from typing import Any

from conversational_toolkit.retriever.base import Retriever
from conversational_toolkit.vectorstores.base import ChunkMatch, ChunkRecord


class HybridRetriever(Retriever[ChunkMatch]):
    """
    Retriever that fuses results from multiple sub-retrievers with RRF.

    Sub-retrievers can be of any type ('VectorStoreRetriever', 'BM25Retriever', or even other 'HybridRetriever' instances). They are queried in parallel, so latency is bounded by the slowest sub-retriever rather than the sum.

    Attributes:
        retrievers: The sub-retrievers to query.
        rrf_k: RRF damping constant. Higher values reduce the advantage of top-ranked results. The default of 60 is the standard choice from the original RRF paper.
    """

    def __init__(self, retrievers: list[Retriever[Any]], top_k: int, rrf_k: int = 60) -> None:
        super().__init__(top_k)
        self.retrievers = retrievers
        self.rrf_k = rrf_k

    async def retrieve(self, query: str) -> list[ChunkMatch]:
        """Query all sub-retrievers in parallel and return the top 'top_k' RRF-merged results."""
        all_results: list[list[Any]] = await asyncio.gather(*[r.retrieve(query) for r in self.retrievers])
        return self._rrf_merge(all_results)[: self.top_k]

    def _rrf_merge(self, results_per_retriever: list[list[ChunkRecord]]) -> list[ChunkMatch]:
        fused_scores: dict[str, float] = {}
        chunk_map: dict[str, ChunkRecord] = {}

        for ranked_list in results_per_retriever:
            for rank, chunk in enumerate(ranked_list, start=1):
                fused_scores[chunk.id] = fused_scores.get(chunk.id, 0.0) + 1.0 / (self.rrf_k + rank)
                chunk_map[chunk.id] = chunk

        return [
            ChunkMatch(
                id=chunk_map[cid].id,
                title=chunk_map[cid].title,
                content=chunk_map[cid].content,
                mime_type=chunk_map[cid].mime_type,
                metadata=chunk_map[cid].metadata,
                embedding=chunk_map[cid].embedding,
                score=fused_scores[cid],
            )
            for cid in sorted(fused_scores, key=lambda c: fused_scores[c], reverse=True)
        ]
