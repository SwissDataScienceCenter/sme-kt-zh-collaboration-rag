"""
Context window retriever that expands each retrieved chunk with its neighbours.

After the base retriever returns its top-k results, 'ContextWindowRetriever' fetches the adjacent chunks (window_size chunks on each side) from the vector store and stitches them into a single, larger content window before returning.

Requirements:
    - Chunks must have 'chunk_index' (int) and 'source_file' (str) in their metadata. These are set by 'fixed_size_chunks()' and 'paragraph_aware_chunks()' in feature0_ingestion.py, but NOT by the default header-based PDFChunker.
    - The vector store must implement 'get_chunks_by_filter()' (ChromaDBVectorStore and PGVectorStore both do).

If a chunk lacks the required metadata fields, it is returned unchanged.
"""

import asyncio

from conversational_toolkit.retriever.base import Retriever
from conversational_toolkit.vectorstores.base import ChunkMatch, VectorStore


class ContextWindowRetriever(Retriever[ChunkMatch]):
    """
    Retriever that widens each result's context by including neighbouring chunks.

    Attributes:
        retriever: The base retriever that produces the initial ranked list.
        vector_store: The store used to look up neighbours by metadata filter.
        window_size: How many chunks to include on each side of a retrieved chunk. window_size=1 adds at most one predecessor and one successor.
    """

    def __init__(
        self,
        retriever: Retriever,
        vector_store: VectorStore,
        window_size: int = 1,
        top_k: int = 5,
    ) -> None:
        super().__init__(top_k)
        self.retriever = retriever
        self.vector_store = vector_store
        self.window_size = window_size

    async def retrieve(self, query: str) -> list[ChunkMatch]:
        """Retrieve then expand: fetch base results, then widen each with neighbours."""
        base_chunks = await self.retriever.retrieve(query)
        expanded = await asyncio.gather(*[self._expand(c) for c in base_chunks])
        return list(expanded)[: self.top_k]

    async def _expand(self, chunk: ChunkMatch) -> ChunkMatch:
        """Replace chunk.content with a stitched window including its neighbours."""
        idx = chunk.metadata.get("chunk_index")
        source = chunk.metadata.get("source_file")

        if idx is None or source is None:
            # Chunk was not produced by a position-aware chunker -> return as-is.
            return chunk

        idx = int(idx)
        offsets = [o for o in range(-self.window_size, self.window_size + 1) if o != 0]

        # Fetch all neighbours in parallel.
        neighbour_lists = await asyncio.gather(
            *[
                self.vector_store.get_chunks_by_filter(
                    {
                        "$and": [
                            {"source_file": {"$eq": source}},
                            {"chunk_index": {"$eq": idx + offset}},
                        ]
                    }
                )
                for offset in offsets
            ]
        )
        neighbours = [c for sublist in neighbour_lists for c in sublist]

        if not neighbours:
            return chunk

        # Sort all chunks (neighbours + the retrieved chunk itself) by position.
        all_chunks = sorted(
            [*neighbours, chunk],
            key=lambda c: int(c.metadata.get("chunk_index", 0)),
        )
        expanded_content = "\n\n".join(c.content for c in all_chunks)

        return ChunkMatch(
            id=chunk.id,
            title=chunk.title,
            content=expanded_content,
            mime_type=chunk.mime_type,
            metadata={**chunk.metadata, "context_window_size": self.window_size},
            embedding=chunk.embedding,
            score=chunk.score,
        )
