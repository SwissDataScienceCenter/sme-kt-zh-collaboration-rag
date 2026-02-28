"""
Baseline RAG pipeline.

Each pipeline stage is an independent function so you can run and inspect
individual steps without executing the full pipeline. loguru logs the
intermediate state at every stage.

Steps at a glance:
    1  load_chunks()         — Load PDFs, split into header-based chunks
    2  build_vector_store()  — Embed chunks and persist to ChromaDB
    3  inspect_retrieval()   — Run semantic search and print results
    4  build_agent()         — Assemble the RAG agent from the vector store
    5  ask()                 — Send a query and return the answer

LLM backends (BACKEND must be set explicitly — there is no default):
    ollama  — local Ollama server at http://localhost:11434
    openai  — requires OPENAI_API_KEY (env var or /secrets/OPENAI_API_KEY file)

Data & vector store:
    PDFs are read from <project-root>/data/.
    The vector store is written to <project-root>/backend/data_vs.db.
    Set reset_vs=True (or RESET_VS=1) to rebuild the store from scratch.
    Re-embedding is skipped on subsequent runs if the store already exists.

Usage:
    BACKEND must always be provided explicitly:
        BACKEND=ollama python -m sme_kt_zh_collaboration_rag.feature0_baseline_rag
        BACKEND=openai python -m sme_kt_zh_collaboration_rag.feature0_baseline_rag

    Override the query or model at runtime:
        QUERY="What is the carbon footprint of wood pallets?" \\
        BACKEND=openai python -m sme_kt_zh_collaboration_rag.feature0_baseline_rag

        MODEL=gpt-4o   BACKEND=openai python -m sme_kt_zh_collaboration_rag.feature0_baseline_rag
        MODEL=llama3.2 BACKEND=ollama python -m sme_kt_zh_collaboration_rag.feature0_baseline_rag
"""

import asyncio
import hashlib
import os
from collections import Counter
from pathlib import Path

from loguru import logger

from conversational_toolkit.agents.base import QueryWithContext
from conversational_toolkit.agents.rag import RAG
from conversational_toolkit.chunking.base import Chunk
from conversational_toolkit.chunking.excel_chunker import ExcelChunker
from conversational_toolkit.chunking.markdown_chunker import MarkdownChunker
from conversational_toolkit.chunking.pdf_chunker import PDFChunker
from conversational_toolkit.embeddings.sentence_transformer import (
    SentenceTransformerEmbeddings,
)
from conversational_toolkit.llms.base import LLM, LLMMessage
from conversational_toolkit.llms.local_llm import LocalLLM
from conversational_toolkit.llms.ollama import OllamaLLM
from conversational_toolkit.llms.openai import OpenAILLM
from conversational_toolkit.retriever.vectorstore_retriever import VectorStoreRetriever
from conversational_toolkit.vectorstores.base import ChunkMatch
from conversational_toolkit.vectorstores.chromadb import ChromaDBVectorStore

# Paths and defaults
_ROOT = Path(__file__).parents[3]  # <project-root>/
DATA_DIR = _ROOT / "data"
VS_PATH = _ROOT / "backend" / "data_vs.db"

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
RETRIEVER_TOP_K = 5
SEED = 42
MAX_FILES = 5

SYSTEM_PROMPT = (
    "You are a helpful AI assistant specialised in sustainability and product compliance for PrimePack AG.\n\n"
    "You will receive document excerpts relevant to the user's question. "
    "Produce the best possible answer using only the information in those excerpts.\n\n"
    "Rules:\n"
    "- Use the provided excerpts as your only source of truth. Do not rely on outside knowledge.\n"
    "- Use all relevant excerpts when forming your answer.\n"
    "- If the answer cannot be found in the excerpts, clearly say that you do not know.\n"
    "- Always cite the source document for any claim you make.\n"
    "- If excerpts contain conflicting information, report both values and flag the conflict.\n"
    "- Distinguish between third-party verified claims (EPDs) and self-declared supplier claims."
)

_CHUNKERS: dict[str, PDFChunker | ExcelChunker | MarkdownChunker] = {
    ".pdf": PDFChunker(),
    ".xlsx": ExcelChunker(),
    ".xls": ExcelChunker(),
    ".md": MarkdownChunker(),
    ".txt": MarkdownChunker(),
}
_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".tiff", ".bmp", ".webp"}


def _get_secret(name: str) -> str:
    """Load a secret from a Renku secret file or an environment variable.

    Checks in order:
    1. /secrets/<name> — Renku secret file
    2. <name> environment variable

    Raises ValueError if neither is available.
    """
    secret_file = Path(f"/secrets/{name}")
    if secret_file.exists():
        return secret_file.read_text().strip()
    key = os.environ.get(name, "")
    if not key:
        raise ValueError(
            f"{name} not found. Either:\n"
            f"  - Add it as a Renku secret at /secrets/{name} (see Renku_README.md), or\n"
            f"  - Set the {name} environment variable."
        )
    return key


def build_llm(
    backend: str,
    model_name: str | None = None,
    temperature: float = 0.3,
    response_format=None,
) -> LLM:
    """Instantiate the LLM for the requested backend.

    Args:
        backend:     LLM backend — must be one of 'ollama', 'openai', or 'qwen'. No default.
        model_name:  Model to use. Falls back to the per-backend default when None.
        temperature: Sampling temperature.
        response_format: Optional parameter to specify the desired response format (e.g., "json"). Supported by some backends.

    For 'openai', the key is loaded from /secrets/OPENAI_API_KEY or the OPENAI_API_KEY env var.
    """
    backend = backend.lower().strip()
    match backend:
        case "openai":
            name = model_name or "gpt-4o-mini"
            logger.info(f"LLM backend: OpenAI ({name})")
            return OpenAILLM(
                model_name=name,
                temperature=temperature,
                seed=SEED,
                openai_api_key=_get_secret("OPENAI_API_KEY"),
                response_format=response_format,
            )
        case "qwen":
            name = model_name or "Qwen/Qwen3-32B-AWQ"
            logger.info(f"LLM backend: SDSC Qwen ({name})")
            return LocalLLM(
                model_name=name,
                base_url="https://vllm-gateway-runai-codev-llm.inference.compute.datascience.ch/v1",
                api_key=_get_secret("SDSC_QWEN3_32B_AWQ"),
                temperature=temperature,
                seed=SEED,
            )
        case "ollama":
            name = model_name or "mistral-nemo:12b"
            logger.info(f"LLM backend: Ollama ({name})")
            return OllamaLLM(
                model_name=name,
                temperature=temperature,
                seed=SEED,
                tools=None,
                tool_choice=None,
                response_format=response_format,
                host=None,  # default http://localhost:11434
            )
        case _:
            raise ValueError(
                f"Unsupported backend {backend!r}. Choose 'openai', 'ollama', or 'qwen'."
            )


def file_hash(path: Path) -> str:
    """SHA-256 fingerprint of a file's raw bytes."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def get_existing_hashes(db_path: Path = VS_PATH) -> set[str]:
    """Return file hashes already present in the vector store."""
    if not db_path.exists():
        return set()
    vs = ChromaDBVectorStore(db_path=str(db_path))
    result = vs.collection.get(include=["metadatas"])
    return {m["file_hash"] for m in result["metadatas"] if "file_hash" in m}


def load_chunks(max_files: int | None = None, existing_hashes: set[str] | None = None) -> list[Chunk]:
    """Load documents from DATA_DIR and split them into chunks.

    Supported formats:
        .pdf: converted to Markdown via pymupdf4llm, split on headings
        .xlsx, .xls: one chunk per sheet (Markdown table)

    Unsupported formats (e.g. standalone images) are logged as warnings and skipped.
    Images embedded inside PDFs are not extracted as text by default!

    Pass 'max_files' to cap the total number of files processed. Useful for quick
    iteration during development before scaling to all files.
    """
    all_chunks: list[Chunk] = []
    all_files = sorted(f for f in DATA_DIR.iterdir() if f.is_file())

    if max_files is not None:
        all_files = all_files[:max_files]
        print(len(all_files))

    for f in all_files:
        ext = f.suffix.lower()
        if ext not in _CHUNKERS:
            if ext in _IMAGE_EXTENSIONS:
                logger.warning(f"Skipping image file (not supported): {f.name}")
            else:
                logger.warning(f"Skipping unsupported file type {ext!r}: {f.name}")

    supported_files = [f for f in all_files if f.suffix.lower() in _CHUNKERS]
    logger.info(f"Chunking {len(supported_files)} files from {DATA_DIR}")

    seen_hashes: set[str] = set()
    for file_path in supported_files:
        hash_value = file_hash(file_path)
        if existing_hashes is not None and hash_value in existing_hashes:
            logger.info(f"Skipping {file_path.name!r} — already in store (hash={hash_value[:8]}…)")
            continue
        if hash_value in seen_hashes:
            logger.warning(f"Skipping {file_path.name!r} — duplicate content in current batch (hash={hash_value[:8]}…)")
            continue
        seen_hashes.add(hash_value)
        chunker = _CHUNKERS[file_path.suffix.lower()]
        try:
            file_chunks = chunker.make_chunks(str(file_path))
            for chunk in file_chunks:
                chunk.metadata["file_hash"] = hash_value
                chunk.metadata["source_file"] = file_path.name
                chunk.metadata["source"] = file_path.name
                chunk.metadata["title"] = chunk.title
            all_chunks.extend(file_chunks)
            logger.debug(f"  {file_path.name}: {len(file_chunks)} chunks")
        except Exception as exc:
            logger.warning(f"Skipping {file_path.name}: {exc}")

    logger.info(f"Done, {len(all_chunks)} chunks total")
    return all_chunks


def inspect_chunks(chunks: list[Chunk], sample_size: int = 5) -> None:
    """Print a statistical summary and sampled content for visual inspection.

    Call this after 'load_chunks' to verify that PDFs parsed correctly
    and that the chunk granularity looks reasonable before spending time on
    embedding.
    """
    counts = Counter(c.metadata.get("source_file", "unknown") for c in chunks)
    logger.info("------ Chunk inspection -------")
    logger.info(f"Total chunks: {len(chunks)}; Source files: {len(counts)}")
    for fname, n in sorted(counts.items()):
        logger.info(f"{fname}: {n} chunks")
    logger.info(f"Sample (first {sample_size}):")
    for chunk in chunks[:sample_size]:
        source = chunk.metadata.get("source_file", "?")
        logger.info(f"Source and title: [{source}] {chunk.title!r}")
        logger.info(f"Chunk content: {chunk.content[:200].strip()!r}")


async def build_vector_store(
    chunks: list[Chunk],
    embedding_model: SentenceTransformerEmbeddings,
    db_path: Path = VS_PATH,
    reset: bool = False,
) -> ChromaDBVectorStore:
    """Embed 'chunks' and persist them in a ChromaDB vector store.

    Set 'reset=True' to delete and rebuild the store from scratch. Leave
    'reset=False' (default) to reuse an existing store, embedding all documents
    takes time; skipping it on subsequent runs saves time.
    """
    if reset and db_path.exists():
        import shutil
        shutil.rmtree(db_path)
        logger.info(f"Deleted existing vector store at {db_path}")

    vector_store = ChromaDBVectorStore(db_path=str(db_path))
    

    # Group chunks by file hash for per-file deduplication
    chunks_by_hash: dict[str, list[Chunk]] = {}
    for chunk in chunks:
        h = chunk.metadata.get("file_hash", "unknown")
        chunks_by_hash.setdefault(h, []).append(chunk)

    # Warn about same-content files in the current batch
    for hash_value, file_chunks in chunks_by_hash.items():
        sources = list(dict.fromkeys(c.metadata.get("source_file", "?") for c in file_chunks))
        if len(sources) > 1:
            logger.warning(f"Duplicate content detected across files (hash={hash_value[:8]}…): {sources} — only ingesting once.")

    new_chunks: list[Chunk] = []
    skipped_files = 0
    skipped_chunks = 0
    for hash_value, file_chunks in chunks_by_hash.items():
        existing = vector_store.collection.get(where={"file_hash": hash_value}, limit=1)
        if existing["ids"]:
            source = file_chunks[0].metadata.get("source_file", "?")
            logger.info(f"Skipping {source!r} — already in store (hash={hash_value[:8]}…)")
            skipped_files += 1
            skipped_chunks += len(file_chunks)
        else:
            new_chunks.extend(file_chunks)
    logger.info(
        f"Deduplication: {skipped_files} file(s) / {skipped_chunks} chunk(s) skipped, "
        f"{len(chunks_by_hash) - skipped_files} file(s) / {len(new_chunks)} chunk(s) to embed."
    )

    if not new_chunks:
        logger.info("All files already in store — nothing to embed.")
        return vector_store

    logger.info(f"Embedding {len(new_chunks)} new chunks with {embedding_model.model_name!r} …")
    embeddings = await embedding_model.get_embeddings([c.content for c in new_chunks])
    logger.info(f"Embedding matrix: shape={embeddings.shape}  dtype={embeddings.dtype}")
    await vector_store.insert_chunks(chunks=new_chunks, embedding=embeddings)
    logger.info(f"Done! Vector store written to {db_path}")
    return vector_store


async def inspect_retrieval(
    query: str,
    vector_store: ChromaDBVectorStore,
    embedding_model: SentenceTransformerEmbeddings,
    top_k: int = RETRIEVER_TOP_K,
) -> list[ChunkMatch]:
    """Run semantic retrieval and print the results before the LLM sees anything.

    This is the most important diagnostic step: if the chunks returned here are
    wrong, the final answer will be wrong regardless of the model. Run this step
    in isolation to tune 'RETRIEVER_TOP_K', experiment with query phrasing, or compare
    different embedding models.

    # To add lexical (BM25) or hybrid (semantic + lexical) retrieval, replace
    'VectorStoreRetriever' with 'HybridRetriever([semantic, bm25], top_k=top_k)'.
    'BM25Retriever' requires a 'list[ChunkRecord]' corpus -> pass the records
    retrieved from ChromaDB or, after a full store insert, re-fetch them with
    'vector_store.get_chunks_by_embedding(zero_vector, top_k=N)'.
    """
    retriever = VectorStoreRetriever(embedding_model, vector_store, top_k=top_k)
    results = await retriever.retrieve(query)

    logger.info(f"Retrieval for query: {query!r}")
    print(
        f"\nTop-{top_k} retrieved chunks (returned={len(results)}; showing a maximum of 1000 content characters):"
    )
    for i, r in enumerate(results, 1):
        src = r.metadata.get("source_file", "?")
        print(f"  [{i}] score={r.score:.4f}  file={src!r}  title={r.title!r}")
        print(f"       {r.content[:1000].strip()!r}")

    return results


def build_agent(
    vector_store: ChromaDBVectorStore,
    embedding_model: SentenceTransformerEmbeddings,
    llm: LLM,
    top_k: int,
    system_prompt: str,
    number_query_expansion: int = 0,
) -> RAG:
    """Assemble the RAG agent from a pre-built vector store and LLM.

    'number_query_expansion' > 0 expands the user query into N related English
    sub-queries, retrieves for each separately, and merges results with RRF
    before generation. Useful for broad or ambiguous questions but adds one
    LLM call per expansion.
    """
    retriever = VectorStoreRetriever(embedding_model, vector_store, top_k=top_k)
    agent = RAG(
        llm=llm,
        utility_llm=llm,
        system_prompt=system_prompt,
        retrievers=[retriever],
        number_query_expansion=number_query_expansion,
    )
    logger.info(
        f"RAG agent ready (top_k={top_k}  query_expansion={number_query_expansion})"
    )
    return agent


async def ask(
    agent: RAG,
    query: str,
    history: list[LLMMessage] | None = None,
) -> str:
    """Send 'query' to the RAG agent and log the answer plus cited sources.

    Returns the answer string so callers can store or post-process it.
    Pass 'history' to simulate a multi-turn conversation: the agent will
    rewrite the query to be self-contained before retrieval.
    """
    logger.info(f"Query: {query!r}")
    response = await agent.answer(QueryWithContext(query=query, history=history or []))

    logger.info("Answer:")
    print(f"{response.content}")
    print(f"Sources ({len(response.sources)}):")
    for src in response.sources:
        source_file = src.metadata.get("source_file", "?")  # type: ignore[union-attr]
        print(f"  {source_file!r}  |  {src.title!r}")

    return response.content


async def run_pipeline(
    backend: str,
    model_name: str | None = None,
    query: str = "What sustainability certifications do the pallets have?",
    reset_vs: bool = False,
) -> str:
    """Run the full five-step pipeline and return the final answer.

    Args:
        backend:    LLM backend — must be one of 'ollama', 'openai', or 'qwen'. No default.
        model_name: Model override, see build_llm() for per-backend defaults
        query:      The question to ask
        reset_vs:   Rebuild the vector store from scratch even if one exists

    Returns:
        The final answer string from the RAG agent.
    """
    logger.info("Starting Baseline RAG pipeline")
    logger.info(
        f"backend={backend!r}  model={model_name!r}  max_files={MAX_FILES}  reset_vs={reset_vs}  top_k={RETRIEVER_TOP_K}"
    )

    # Step 1: Chunking (skip files already in the store)
    existing_hashes = get_existing_hashes() if not reset_vs else set()
    chunks = load_chunks(max_files=MAX_FILES, existing_hashes=existing_hashes)
    inspect_chunks(chunks)

    # Step 2: Embedding + vector store
    embedding_model = SentenceTransformerEmbeddings(model_name=EMBEDDING_MODEL)
    vector_store = await build_vector_store(chunks, embedding_model, reset=reset_vs)

    # Step 3: Inspect retrieval before the LLM is involved
    await inspect_retrieval(query, vector_store, embedding_model)

    # Step 4: Build agent
    llm = build_llm(backend, model_name=model_name)
    agent = build_agent(
        vector_store,
        embedding_model,
        llm,
        top_k=RETRIEVER_TOP_K,
        system_prompt=SYSTEM_PROMPT,
    )

    # Step 5: Generate answer
    answer = await ask(agent, query)

    logger.info("Baseline RAG pipeline done")
    return answer


if __name__ == "__main__":
    _backend = os.getenv("BACKEND")
    if not _backend:
        raise SystemExit(
            "The BACKEND environment variable is not set.\n"
            "Choose one of: ollama, openai, qwen\n"
            "Example: BACKEND=ollama python -m sme_kt_zh_collaboration_rag.feature0_baseline_rag"
        )
    asyncio.run(
        run_pipeline(
            backend=_backend,
            model_name=os.getenv("MODEL") or None,
            query=os.getenv("QUERY", "What materials is the Lara pallet made out of?"),
            reset_vs=os.getenv("RESET_VS", "0") == "1",
        )
    )
