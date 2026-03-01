"""
Retriever abstractions.

A retriever accepts a natural-language query and returns a ranked list of document chunks. 'Retriever' is generic over 'T_co' (covariant, bounded by 'Chunk') so that a 'Retriever[ChunkMatch]' can be assigned where a 'Retriever[ChunkRecord]' is expected without unsafe casts.

Concrete implementations: 'VectorStoreRetriever', 'BM25Retriever', 'HybridRetriever',
'RerankingRetriever'.
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic

from conversational_toolkit.chunking.base import Chunk

T_co = TypeVar("T_co", bound=Chunk, covariant=True)


class Retriever(ABC, Generic[T_co]):
    """
    Abstract base class for document retrievers.

    'T_co' is covariant because the retriever only produces values of that type (in the return position of 'retrieve') and never consumes them, which makes the covariant subtyping relationship safe and useful in practice.

    Attributes:
        top_k: Maximum number of chunks to return per query.
    """

    def __init__(self, top_k: int):
        self.top_k = top_k

    @abstractmethod
    async def retrieve(self, query: str) -> list[T_co]:
        """Return up to 'top_k' chunks most relevant to 'query'."""
        pass
