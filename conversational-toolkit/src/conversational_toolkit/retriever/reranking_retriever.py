"""
LLM-based reranking retriever.

'RerankingRetriever' is a two-stage retriever: it first fetches a larger candidate pool from a base retriever, then asks an LLM to re-order the candidates by relevance to the query. This is useful when the base retriever (embedding similarity or BM25) retrieves the right documents but ranks them suboptimally.

Design note: configure the base retriever with 'top_k = candidate_pool_size' (e.g. 20) and set 'RerankingRetriever.top_k' to the final number you want returned (e.g. 5). The two 'top_k' values serve different purposes and are intentionally separate.

If the LLM call fails or returns unparseable JSON the retriever falls back to the original ranking from the base retriever, so the pipeline never breaks.
"""

import json
from textwrap import dedent
from typing import Any

from loguru import logger

from conversational_toolkit.llms.base import LLM, LLMMessage, Roles
from conversational_toolkit.retriever.base import Retriever
from conversational_toolkit.vectorstores.base import ChunkMatch, ChunkRecord


class RerankingRetriever(Retriever[ChunkMatch]):
    """
    Two-stage retriever that uses an LLM to rerank a candidate pool.

    The base retriever should be configured with a 'top_k' equal to the desired candidate pool size (typically 3-4x the final 'top_k'). The LLM receives the query and truncated chunk contents and returns a ranked list of indices as JSON. The score assigned to each result is a linear decay from 1.0 (rank 1) to 0.0 (last rank).

    Attributes:
        retriever: The base retriever that supplies the candidate pool.
        llm: The language model used for reranking. A fast, cheap model is recommended since the reranking prompt is simple.
    """

    def __init__(self, retriever: Retriever[Any], llm: LLM, top_k: int) -> None:
        super().__init__(top_k)
        self.retriever = retriever
        self.llm = llm

    async def retrieve(self, query: str) -> list[ChunkMatch]:
        """Fetch candidates from the base retriever and rerank them with the LLM."""
        candidates: list[ChunkRecord] = await self.retriever.retrieve(query)  # type: ignore[assignment]
        if not candidates:
            return []

        ranked_indices = await self._llm_rerank(query, candidates)
        n = len(ranked_indices)
        results: list[ChunkMatch] = []
        for position, original_idx in enumerate(ranked_indices[: self.top_k]):
            chunk = candidates[original_idx]
            score = (n - position) / n  # linear decay: 1.0 at rank 1, approaching 0 at rank n
            results.append(
                ChunkMatch(
                    id=chunk.id,
                    title=chunk.title,
                    content=chunk.content,
                    mime_type=chunk.mime_type,
                    metadata=chunk.metadata,
                    embedding=chunk.embedding,
                    score=score,
                )
            )
        return results

    async def _llm_rerank(self, query: str, candidates: list[ChunkRecord]) -> list[int]:
        """Ask the LLM to rank the candidates and return a list of original indices.

        Returns the original order as a fallback if the LLM call fails or produces invalid JSON.
        """
        numbered = "\n\n".join(
            f"[{i}] {chunk.title or '(no title)'}\n{chunk.content[:400]}" for i, chunk in enumerate(candidates)
        )
        prompt = dedent(f"""
            Query: {query}

            Rank the following {len(candidates)} document chunks from most to least relevant
            to the query. Output only a JSON object with a single key "ranking" whose value
            is a list of the chunk indices ordered from most to least relevant.

            Chunks:
            {numbered}

            Output format: {{"ranking": [most_relevant_index, second_index, ...]}}
        """).strip()

        messages = [
            LLMMessage(
                role=Roles.SYSTEM,
                content="You are an expert at assessing document relevance. Output only valid JSON.",
            ),
            LLMMessage(role=Roles.USER, content=prompt),
        ]

        try:
            response = await self.llm.generate(messages)
            data = json.loads(response.content)
            ranking: list[int] = [int(i) for i in data["ranking"] if 0 <= int(i) < len(candidates)]
            # Append any missing indices at the end (graceful fallback for partial rankings)
            seen = set(ranking)
            ranking += [i for i in range(len(candidates)) if i not in seen]
            return ranking
        except Exception as exc:
            logger.warning(f"RerankingRetriever LLM call failed, using original order: {exc}")
            return list(range(len(candidates)))
