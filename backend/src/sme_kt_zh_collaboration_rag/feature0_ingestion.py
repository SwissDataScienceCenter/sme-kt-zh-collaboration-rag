"""
Feature Track 1: Document Ingestion & Chunking

Explores and compares three chunking strategies:
    1. header_based     — PDFChunker splits on Markdown headings (one chunk per section)
    2. fixed_size       — Fixed character window with overlap (predictable sizes)
    3. paragraph_aware  — Merge paragraphs until a target size is reached

The embedding model (all-MiniLM-L6-v2) has a 256-token limit. Chunks that exceed
this are silently truncated — information at the end is lost. Visualising chunk-size
distributions before embedding exposes this problem and motivates switching to
models with higher token limits (e.g. OpenAI text-embedding-3-small: 8 191 tokens).
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional

import pymupdf4llm  # type: ignore[import-untyped]
from loguru import logger

from conversational_toolkit.chunking.base import Chunk
from conversational_toolkit.chunking.pdf_chunker import PDFChunker


@dataclass
class ChunkStats:
    strategy: str
    total_chunks: int
    avg_chars: float
    min_chars: int
    max_chars: int
    median_chars: int
    over_limit: int  # chunks estimated >256 tokens (embedding model limit)

    def __str__(self) -> str:
        return (
            f"{self.strategy:<22} chunks={self.total_chunks:>4}, "
            f"avg={self.avg_chars:>6.0f}, min={self.min_chars:>5}, "
            f"max={self.max_chars:>6}, >256tok={self.over_limit:>4}"
        )


def estimate_tokens(text: str) -> int:
    """Rough estimate: 1 token ≈ 4 characters (good enough for sizing decisions)."""
    return len(text) // 4


def analyze_chunks(chunks: list[Chunk], strategy_name: str) -> ChunkStats:
    """Compute size statistics for a list of chunks."""
    if not chunks:
        return ChunkStats(strategy_name, 0, 0.0, 0, 0, 0, 0)
    lengths = sorted(len(c.content) for c in chunks)
    n = len(lengths)
    over = sum(1 for c in chunks if estimate_tokens(c.content) > 256)
    return ChunkStats(
        strategy=strategy_name,
        total_chunks=n,
        avg_chars=sum(lengths) / n,
        min_chars=lengths[0],
        max_chars=lengths[-1],
        median_chars=lengths[n // 2],
        over_limit=over,
    )


def char_histogram(chunks: list[Chunk], bins: int = 10, width: int = 40) -> str:
    """Return a simple ASCII histogram of chunk character lengths."""
    lengths = [len(c.content) for c in chunks]
    if not lengths:
        return "(no chunks)"
    lo, hi = min(lengths), max(lengths)
    if lo == hi:
        return f"All chunks: {lo} chars"
    step = (hi - lo) / bins
    counts = [0] * bins
    for length in lengths:
        idx = min(int((length - lo) / step), bins - 1)
        counts[idx] += 1
    max_count = max(counts)
    lines = []
    for i, c in enumerate(counts):
        label = f"{lo + i * step:>6.0f}-{lo + (i + 1) * step:<6.0f}"
        bar = "█" * int(c / max_count * width)
        lines.append(f"  {label} | {bar} {c}")
    return "\n".join(lines)


def header_based_chunks(file_path: str) -> list[Chunk]:
    """Header-based chunking (PDFChunker default): one chunk per Markdown heading section."""
    return PDFChunker().make_chunks(file_path)


def fixed_size_chunks(
    file_path: str,
    chunk_size: int = 800,  # in characters
    overlap: int = 100,  # in characters
) -> list[Chunk]:
    """
    Fixed-size character chunking with overlap.

    Produces predictable chunk sizes regardless of document structure.
    Overlap preserves context across chunk boundaries.
    Risk: may cut mid-sentence.
    """
    markdown: str = pymupdf4llm.to_markdown(file_path)  # type: ignore[assignment]
    chunks: list[Chunk] = []
    start = 0
    idx = 0
    while start < len(markdown):
        end = min(start + chunk_size, len(markdown))
        content = markdown[start:end]
        chunks.append(
            Chunk(
                title=f"chunk_{idx:04d}",
                content=content,
                mime_type="text/markdown",
                metadata={"chunk_index": idx, "start_char": start, "end_char": end},
            )
        )
        start += chunk_size - overlap
        idx += 1
    return chunks


def paragraph_aware_chunks(file_path: str, target_chars: int = 600) -> list[Chunk]:
    """
    Paragraph-aware chunking: split on blank lines (\\n\\n), then merge short
    paragraphs until the target character count is reached.

    Produces semantically coherent chunks without hard size limits per paragraph.
    """
    markdown: str = pymupdf4llm.to_markdown(file_path)  # type: ignore[assignment]
    paragraphs = [p.strip() for p in markdown.split("\n\n") if p.strip()]
    chunks: list[Chunk] = []
    current: list[str] = []
    current_len = 0
    idx = 0
    for para in paragraphs:
        if current_len + len(para) > target_chars and current:
            content = "\n\n".join(current)
            chunks.append(
                Chunk(
                    title=f"para_chunk_{idx:04d}",
                    content=content,
                    mime_type="text/markdown",
                    metadata={"chunk_index": idx},
                )
            )
            idx += 1
            current = [para]
            current_len = len(para)
        else:
            current.append(para)
            current_len += len(para)
    if current:
        chunks.append(
            Chunk(
                title=f"para_chunk_{idx:04d}",
                content="\n\n".join(current),
                mime_type="text/markdown",
                metadata={"chunk_index": idx},
            )
        )
    return chunks


def compare_strategies(file_path: str) -> dict[str, tuple[list[Chunk], ChunkStats]]:
    """
    Run all three chunking strategies on a single file and return
    {strategy_name: (chunks, stats)} for inspection and comparison.
    """
    logger.info(f"Comparing chunking strategies on: {Path(file_path).name}")
    results: dict[str, tuple[list[Chunk], ChunkStats]] = {}

    strategies: list[tuple[str, Callable[..., list[Chunk]], dict[str, Any]]] = [
        ("header_based", header_based_chunks, {}),
        ("fixed_size_800", fixed_size_chunks, {"chunk_size": 800, "overlap": 100}),
        ("paragraph_600", paragraph_aware_chunks, {"target_chars": 600}),
    ]
    for name, fn, kwargs in strategies:
        chunks = fn(file_path, **kwargs)
        stats = analyze_chunks(chunks, name)
        results[name] = (chunks, stats)
        logger.info(f"  {stats}")

    return results


def print_comparison_table(results: dict[str, tuple[list[Chunk], ChunkStats]]) -> None:
    """Print a compact comparison table to stdout."""
    header = f"{'Strategy':<22}  {'Chunks':>6}  {'Avg chars':>9}  {'Min':>5}  {'Max':>6}  {'>256tok':>7}"
    print(header)
    print("-" * len(header))
    for _, (_, stats) in results.items():
        print(str(stats))


def validate_chunk_size(
    file_path: str, test_chunker: Optional[Callable[..., list[Chunk]]] = None
) -> dict[str, tuple[list[Chunk], ChunkStats, str]]:
    """Run the three built-in chunkers (and an optional `test_chunker`) on
    `file_path` and return validation stats.

    Prints `analyze_chunks` summary and the `char_histogram` output for each chunker.
    """
    strategies: list[tuple[str, Callable[..., list[Chunk]], dict[str, Any]]] = [
        ("header_based", header_based_chunks, {}),
        ("fixed_size_800", fixed_size_chunks, {"chunk_size": 800, "overlap": 100}),
        ("paragraph_600", paragraph_aware_chunks, {"target_chars": 600}),
    ]
    if test_chunker is not None:
        strategies.append(("test_chunker", test_chunker, {}))

    results: dict[str, tuple[list[Chunk], ChunkStats, str]] = {}
    for name, fn, kwargs in strategies:
        chunks = fn(file_path, **kwargs)
        stats = analyze_chunks(chunks, name)
        hist = char_histogram(chunks)
        # Log a compact one-line summary and print the histogram for inspection
        logger.info(f"Validation - {stats}")
        print(f"\n=== {name} ===")
        print(str(stats))
        print("\nChunk size histogram:")
        print(hist)

        results[name] = (chunks, stats, hist)

    return results
