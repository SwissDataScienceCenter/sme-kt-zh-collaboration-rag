"""
Feature Track 3: Retrieval Strategies

Compares three retrieval approaches that go beyond single-query semantic search:

    1. baseline         — single query -> top-k semantic (VectorStoreRetriever)
    2. bm25             — keyword retrieval (BM25Okapi, no embedding)
    3. hybrid           — semantic + BM25 fused with RRF (HybridRetriever)
    4. metadata_filter  — semantic search restricted to a specific subset of documents

BM25 catches exact keyword matches (product IDs, certification numbers, acronyms) that semantic search misses. Hybrid combines both signals at no extra LLM cost. Metadata filtering lets callers scope retrieval to a known document when the query is document-specific (e.g. "summarise the tesa EPD").
"""

from dataclasses import dataclass, field
from typing import Any, Sequence

import numpy as np
from loguru import logger

from conversational_toolkit.embeddings.sentence_transformer import (
    SentenceTransformerEmbeddings,
)
from conversational_toolkit.retriever.bm25_retriever import BM25Retriever
from conversational_toolkit.retriever.hybrid_retriever import HybridRetriever
from conversational_toolkit.retriever.vectorstore_retriever import VectorStoreRetriever
from conversational_toolkit.vectorstores.base import (
    ChunkMatch,
    ChunkRecord,
)  # ChunkRecord used for corpus type
from conversational_toolkit.vectorstores.chromadb import ChromaDBVectorStore


@dataclass
class RetrievalResult:
    strategy: str
    query_used: str
    chunks: Sequence[ChunkMatch]
    filters: dict[str, Any] | None = field(default=None)

    def top_sources(self, n: int = 5) -> list[str]:
        return [
            f"{c.metadata.get('source_file', '?'):<50} | {c.title!r:.50}"
            for c in self.chunks[:n]
        ]

    def __str__(self) -> str:
        lines = [f"[{self.strategy}]"]
        for s in self.top_sources():
            lines.append(f"  {s}")
        return "\n".join(lines)


async def retrieve_baseline(
    query: str,
    embedding_model: SentenceTransformerEmbeddings,
    vector_store: ChromaDBVectorStore,
    top_k: int = 5,
) -> RetrievalResult:
    """Single-query semantic retrieval, the reference point for all comparisons."""
    retriever = VectorStoreRetriever(embedding_model, vector_store, top_k=top_k)
    chunks = await retriever.retrieve(query)
    return RetrievalResult("baseline", query, chunks)


async def retrieve_bm25(
    query: str,
    corpus: list[ChunkRecord],
    top_k: int = 5,
) -> RetrievalResult:
    """Pure BM25 keyword retrieval -> no embedding, scores by term frequency x IDF."""
    retriever = BM25Retriever(corpus=corpus, top_k=top_k)
    chunks = await retriever.retrieve(query)
    return RetrievalResult("bm25", query, chunks)


async def retrieve_hybrid(
    query: str,
    embedding_model: SentenceTransformerEmbeddings,
    vector_store: ChromaDBVectorStore,
    corpus: list[ChunkRecord],
    top_k: int = 5,
    rrf_k: int = 60,
) -> RetrievalResult:
    """Semantic + BM25 fused with Reciprocal Rank Fusion (RRF)."""
    semantic = VectorStoreRetriever(embedding_model, vector_store, top_k=top_k)
    bm25 = BM25Retriever(corpus=corpus, top_k=top_k)
    hybrid = HybridRetriever(retrievers=[semantic, bm25], top_k=top_k, rrf_k=rrf_k)
    chunks = await hybrid.retrieve(query)
    return RetrievalResult("hybrid", query, chunks)


async def retrieve_with_metadata_filter(
    query: str,
    embedding_model: SentenceTransformerEmbeddings,
    vector_store: ChromaDBVectorStore,
    filters: dict[str, Any],
    top_k: int = 5,
) -> RetrievalResult:
    """Semantic retrieval restricted to chunks matching 'filters'.

    Useful when the caller already knows which document(s) are relevant -> for example, "what are the transport emissions in the tesa EPD?" can be scoped to the tesa source file to avoid noise from other products.

    'filters' uses ChromaDB filter syntax, e.g.:
        {"source_file": {"$eq": "EPD_tesa.pdf"}}
        {"mime_type": {"$eq": "text/markdown"}}

    For compound conditions use '$and' / '$or':
        {"$and": [{"source_file": {"$eq": "A.pdf"}},
                  {"source_file": {"$eq": "B.pdf"}}]}  # never matches — use $or
    """
    embedding = await embedding_model.get_embeddings(query)
    chunks = await vector_store.get_chunks_by_embedding(
        embedding[0], top_k=top_k, filters=filters
    )
    return RetrievalResult("metadata_filter", query, chunks, filters=filters)


async def compare_retrieval_strategies(
    query: str,
    embedding_model: SentenceTransformerEmbeddings,
    vector_store: ChromaDBVectorStore,
    corpus: list[ChunkRecord],
    top_k: int = 5,
    metadata_filters: dict[str, Any] | None = None,
) -> dict[str, RetrievalResult]:
    """Run baseline, BM25, hybrid, and (optionally) metadata-filtered retrieval for one query.

    Returns a dict mapping strategy name -> RetrievalResult. If 'metadata_filters' is None the metadata_filter strategy is skipped.
    """
    logger.info(f"Comparing retrieval strategies for: {query!r}")
    results: dict[str, RetrievalResult] = {}
    results["baseline"] = await retrieve_baseline(
        query, embedding_model, vector_store, top_k
    )
    results["bm25"] = await retrieve_bm25(query, corpus, top_k)
    results["hybrid"] = await retrieve_hybrid(
        query, embedding_model, vector_store, corpus, top_k
    )
    if metadata_filters is not None:
        results["metadata_filter"] = await retrieve_with_metadata_filter(
            query, embedding_model, vector_store, metadata_filters, top_k
        )
    return results


def print_strategy_comparison(
    results: dict[str, RetrievalResult],
    relevant_keywords: list[str],
    top_n: int = 3,
) -> None:
    """Print a side-by-side comparison.

    Chunks whose source/title/content contain a relevant keyword are marked ✓.
    """
    print(f"\nRelevant keywords: {relevant_keywords}")
    print(f"\n{'Strategy':<22}  Top-{top_n} retrieved sources")
    print("─" * 90)
    for name, r in results.items():
        filter_str = f"  (filter: {r.filters})" if r.filters else ""
        print(f"\n{name}{filter_str}")
        for chunk in r.chunks[:top_n]:
            src = chunk.metadata.get("source_file", "?")
            title = chunk.title or "(no title)"
            hit = any(
                kw.lower() in (src + title + chunk.content).lower()
                for kw in relevant_keywords
            )
            marker = "✓" if hit else "·"
            print(f"  {marker}  {src:<48}  {title[:38]!r}")


async def get_corpus_from_vector_store(
    vector_store: ChromaDBVectorStore,
    embedding_model: SentenceTransformerEmbeddings,
    n: int,
) -> list[ChunkRecord]:
    """Fetch a representative corpus from the vector store for BM25 indexing.

    Uses a zero-embedding query to retrieve the n most 'average' chunks.
    """
    zero_vec = np.zeros(
        (await embedding_model.get_embeddings("test")).shape[1], dtype="float32"
    )
    return await vector_store.get_chunks_by_embedding(zero_vec, top_k=n)  # type: ignore[return-value]
