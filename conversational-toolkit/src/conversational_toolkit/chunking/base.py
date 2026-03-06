"""
Document chunking abstractions.

A 'Chunk' is the atomic unit of content flowing through the pipeline: chunkers
produce them, vector stores persist them, and retrievers return them to agents.
'Chunk' is a plain data class with no processing logic so it can be extended by
'ChunkRecord' (adds storage identity) and 'ChunkMatch' (adds a relevance score)
without breaking existing consumers.

Concrete chunkers: 'PDFChunker', 'ExcelChunker', 'JSONLinesChunker'.
"""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class Chunk(BaseModel):
    """
    A single piece of document content ready to be embedded and stored.

    Attributes:
        title: Header or label extracted from the source document.
        content: The content of the chunk.
        mime_type: MIME type of the content (e.g. 'text/markdown', 'image/png').
        metadata: Arbitrary key-value pairs from the source document
            (e.g. page number, chapter hierarchy, sheet name).
    """

    title: str
    content: str
    mime_type: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class Chunker(ABC):
    """
    Abstract base class for document chunkers.

    Each subclass handles a specific file format and produces a list of 'Chunk'
    objects. The loose '*args / **kwargs' signature on 'make_chunks' lets each
    chunker expose format-specific parameters (e.g. the Markdown conversion
    engine for PDFs) without forcing a shared interface for every option.
    """

    @abstractmethod
    def make_chunks(self, *args: Any, **kwargs: Any) -> list[Chunk]:
        """Parse the source file and return a list of 'Chunk' objects."""
        pass
