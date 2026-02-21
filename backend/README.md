# Backend — RAG Pipeline

This package (`sme_kt_zh_collaboration_rag`) contains the notebooks and the supporting Python modules that run the RAG pipeline for the PrimePack AG sustainability use case.

---

## Package structure

```
backend/
├── notebooks/                          # Workshop notebooks (one per feature track)
│   ├── feature0_baseline_rag.ipynb
│   ├── feature1_ingestion_chunking.ipynb
│   └── ...
└── src/sme_kt_zh_collaboration_rag/
    ├── feature0_baseline_rag.py        # Runnable baseline pipeline
    ├── feature1_ingestion.py           # Chunking strategy helpers
    └── ...                             # Further feature modules
```

---

## Feature tracks

### Feature 0 — Baseline RAG Pipeline (`feature0_baseline_rag.ipynb`)

Introduces the five-stage RAG loop and demonstrates it end-to-end against the PrimePack AG corpus.

**Pipeline stages:**

| Step | Function | What it does |
|------|----------|--------------|
| 1 | `load_chunks()` | Load all documents from `data/` and split them into chunks |
| 2 | `build_vector_store()` | Embed chunks and persist to ChromaDB |
| 3 | `inspect_retrieval()` | Run a semantic search and print ranked results with L2 scores |
| 4 | `build_agent()` | Assemble the RAG agent from the retriever and an LLM backend |
| 5 | `ask()` | Send a query and stream the grounded answer |

**Running the pipeline from the command line:**

```bash
# Default (Ollama + mistral-nemo:12b)
python -m sme_kt_zh_collaboration_rag.feature0_baseline_rag

# OpenAI backend
BACKEND=openai python -m sme_kt_zh_collaboration_rag.feature0_baseline_rag

# Custom query
QUERY="Which tape products have a verified EPD?" \
python -m sme_kt_zh_collaboration_rag.feature0_baseline_rag

# Force rebuild of the vector store
RESET_VS=1 python -m sme_kt_zh_collaboration_rag.feature0_baseline_rag

# Override model
MODEL=gpt-4o BACKEND=openai python -m sme_kt_zh_collaboration_rag.feature0_baseline_rag
```

The vector store is written to `backend/data_vs.db`. On subsequent runs, re-embedding is skipped automatically if the store already exists (`RESET_VS=1` forces a rebuild).

---

### Feature 1 — Document Ingestion & Chunking (`feature1_ingestion_chunking.ipynb`)

Explores how chunking strategy affects retrieval quality and walks through the token-limit problem for embedding models.

**Three strategies compared:**

| Strategy | Description |
|----------|-------------|
| Header-based | One chunk per Markdown heading section — preserves document structure |
| Fixed-size | Fixed character window with overlap — predictable, size-uniform |
| Paragraph-aware | Merges paragraphs until a target size is reached — balances structure and size |

**Key concept:** the default embedding model (`all-MiniLM-L6-v2`) has a **256-token limit**. Chunks exceeding this are silently truncated -> information at the tail of a long chunk is lost. The notebook shows how to visualise chunk-size distributions to identify and resolve this problem before embedding.

The supporting module `feature1_ingestion.py` is designed to be imported from the notebook and exposes `ChunkStats` and the three chunking functions for side-by-side comparison.

---

## Further feature tracks

Features 2–5 (Evaluation, Structured Outputs, Query Intelligence, Agent Workflows) will be detailed here soon.

---

## LLM backends

| Backend | Environment variable | Default model |
|---------|---------------------|---------------|
| `ollama` (default) | — | `mistral-nemo:12b` |
| `openai` | `OPENAI_API_KEY` | `gpt-4o-mini` |
| `qwen` | `SDSC_QWEN3_32B_AWQ` | `Qwen3-32B-AWQ` |

Set `BACKEND=<name>` and optionally `MODEL=<model-name>` as environment variables before running any feature module.
