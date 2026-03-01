"""
Vector store abstractions and chunk data models.

'Chunk' is the base document unit. 'ChunkRecord' extends it with the storage
identity ('id') and its embedding vector, representing a chunk as it exists in
the store. 'ChunkMatch' further extends 'ChunkRecord' with a relevance score
returned after a similarity search. This three-level hierarchy preserves type
safety at each stage of the pipeline without duplicating fields.

Concrete implementations: 'ChromaDBVectorStore', 'PGVectorStore'.
"""

from abc import ABC, abstractmethod
from typing import Union, Any

import numpy as np
from numpy.typing import NDArray

from conversational_toolkit.chunking.base import Chunk


class ChunkRecord(Chunk):
    """A 'Chunk' as it is stored in the vector store, with its ID and embedding."""

    id: str
    embedding: list[float]


class ChunkMatch(ChunkRecord):
    """A 'ChunkRecord' returned from a similarity search, augmented with a relevance score."""

    score: float


class VectorStore(ABC):
    """
    Abstract base class for vector store backends.

    Implementations handle insertion, similarity search, and ID-based lookup
    for embedded document chunks. The embedding array passed to 'insert_chunks'
    has shape '(len(chunks), embedding_size)', with rows corresponding to chunks
    in the same order.
    """

    @abstractmethod
    async def insert_chunks(self, chunks: list[Chunk], embedding: NDArray[np.float64]) -> None:
        """Persist 'chunks' together with their pre-computed 'embedding' matrix."""
        pass

    @abstractmethod
    async def get_chunks_by_embedding(
        self, embedding: NDArray[np.float64], top_k: int, filters: dict[str, Any] | None = None
    ) -> list[ChunkMatch]:
        """Return the 'top_k' most similar chunks to 'embedding', optionally filtered by metadata."""
        pass

    @abstractmethod
    async def get_chunks_by_ids(self, chunk_ids: Union[int, list[int]]) -> list[Chunk]:
        """Fetch specific chunks by their stored IDs."""
        pass

    @abstractmethod
    async def get_chunks_by_filter(self, filters: dict[str, Any]) -> list[ChunkRecord]:
        """Return all chunks matching the given metadata filters (no embedding needed)."""
        pass
