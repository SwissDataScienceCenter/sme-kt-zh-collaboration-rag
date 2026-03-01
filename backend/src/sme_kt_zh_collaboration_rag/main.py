"""
Entry point for the SME-KT-ZH Collaboration RAG backend.

Incorporates improvements from the workshop feature tracks:
  - Feature 2: entity-grounded system prompt (VERIFIED / CLAIMED / MISSING labels,
    entity-check rule to prevent substituting similar products)
  - Feature 3a: hybrid retrieval (semantic + BM25 via Reciprocal Rank Fusion),
    which catches exact-match queries (product IDs, certification codes) that
    pure semantic search misses

Environment variables:
    BACKEND: LLM backend -> "openai" (default) or "ollama"
    OPENAI_API_KEY: Required when BACKEND=openai
"""

import asyncio
import os
import pathlib
from pathlib import Path
from textwrap import dedent

import uvicorn
from conversational_toolkit.agents.rag import RAG
from conversational_toolkit.api.server import create_app
from conversational_toolkit.conversation_database.controller import (
    ConversationalToolkitController,
)
from conversational_toolkit.conversation_database.in_memory.conversation import (
    InMemoryConversationDatabase,
)
from conversational_toolkit.conversation_database.in_memory.message import (
    InMemoryMessageDatabase,
)
from conversational_toolkit.conversation_database.in_memory.reactions import (
    InMemoryReactionDatabase,
)
from conversational_toolkit.conversation_database.in_memory.source import (
    InMemorySourceDatabase,
)
from conversational_toolkit.conversation_database.in_memory.user import (
    InMemoryUserDatabase,
)
from conversational_toolkit.embeddings.sentence_transformer import (
    SentenceTransformerEmbeddings,
)
from conversational_toolkit.retriever.bm25_retriever import BM25Retriever
from conversational_toolkit.retriever.hybrid_retriever import HybridRetriever
from conversational_toolkit.retriever.vectorstore_retriever import VectorStoreRetriever
from loguru import logger

from sme_kt_zh_collaboration_rag.feature0_baseline_rag import (
    EMBEDDING_MODEL,
    RETRIEVER_TOP_K,
    VS_PATH,
    build_llm,
    build_vector_store,
    load_chunks,
)
from sme_kt_zh_collaboration_rag.feature3_advanced_retrieval import (
    get_corpus_from_vector_store,
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BACKEND = os.getenv("BACKEND", "openai")

# Renku / local secrets support
_secret = pathlib.Path("/secrets/OPENAI_API_KEY")
if "OPENAI_API_KEY" not in os.environ and _secret.exists():
    os.environ["OPENAI_API_KEY"] = _secret.read_text().strip()

# In-memory database files are written to a local data directory next to this file
_DB_DIR = Path(__file__).parent / "db"
_DB_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# System prompt (Feature 2: entity-grounded to prevent claim laundering)
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = dedent("""
    You are a sustainability compliance assistant for PrimePack AG.
    Answer questions using ONLY the provided sources.

    RULES (apply in order):
    1. Identify the key entity in the question (product name, supplier, product ID).
    2. Check that this exact entity appears in the retrieved sources.
       If it does NOT appear, respond: "The sources do not contain information about
       [entity]. I cannot answer this question." Do not substitute other products.
    3. Distinguish clearly between:
       VERIFIED — backed by a third-party EPD or independent audit
       CLAIMED  — supplier self-declaration, not independently verified
       MISSING  — not found in sources
    4. Label forward-looking targets (e.g. "carbon neutral by 2025") as targets,
       not as current verified status.
    5. Always cite the source document for each claim.
""").strip()

# ---------------------------------------------------------------------------
# Build RAG agent and controller
# ---------------------------------------------------------------------------


async def build_controller() -> ConversationalToolkitController:
    logger.info("Loading documents and building vector store...")
    embedding_model = SentenceTransformerEmbeddings(model_name=EMBEDDING_MODEL)
    chunks = load_chunks()
    vector_store = await build_vector_store(
        chunks, embedding_model, db_path=VS_PATH, reset=False
    )
    logger.info(f"Vector store ready at {VS_PATH}")

    # Feature 3a: hybrid retrieval (semantic + BM25 via Reciprocal Rank Fusion).
    # BM25 catches exact matches (product IDs, certification codes, acronyms) that
    # semantic search misses. Both signals are fused with RRF at no extra LLM cost.
    logger.info("Building BM25 corpus from vector store...")
    corpus = await get_corpus_from_vector_store(vector_store, embedding_model, n=10_000)
    semantic = VectorStoreRetriever(
        embedding_model, vector_store, top_k=RETRIEVER_TOP_K
    )
    bm25 = BM25Retriever(corpus=corpus, top_k=RETRIEVER_TOP_K)
    retriever = HybridRetriever(retrievers=[semantic, bm25], top_k=RETRIEVER_TOP_K)
    logger.info(f"Hybrid retriever ready ({len(corpus)} BM25 corpus chunks)")

    llm = build_llm(backend=BACKEND)
    agent = RAG(
        llm=llm,
        utility_llm=llm,
        system_prompt=SYSTEM_PROMPT,
        retrievers=[retriever],
        number_query_expansion=0,
    )
    logger.info("RAG agent ready (hybrid retrieval, entity-grounded prompt)")

    controller = ConversationalToolkitController(
        conversation_db=InMemoryConversationDatabase(
            str(_DB_DIR / "conversations.json")
        ),
        message_db=InMemoryMessageDatabase(str(_DB_DIR / "messages.json")),
        reaction_db=InMemoryReactionDatabase(str(_DB_DIR / "reactions.json")),
        source_db=InMemorySourceDatabase(str(_DB_DIR / "sources.json")),
        user_db=InMemoryUserDatabase(str(_DB_DIR / "users.json")),
        agent=agent,
    )
    return controller


# ---------------------------------------------------------------------------
# FastAPI application
# Build the app at import time so uvicorn can reference `main:app`.
# The async setup runs inside an asyncio.run() call when started directly.
# ---------------------------------------------------------------------------


def _build_app_sync() -> object:
    """Build the FastAPI app synchronously by running the async setup."""
    controller = asyncio.run(build_controller())
    return create_app(controller=controller)


app = _build_app_sync()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run(
        "sme_kt_zh_collaboration_rag.main:app",
        host="0.0.0.0",
        port=8080,
        reload=False,
        log_level="info",
    )
