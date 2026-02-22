# Backend — RAG Pipeline

This package (`sme_kt_zh_collaboration_rag`) contains the notebooks and the supporting Python modules that run the RAG pipeline for the PrimePack AG sustainability use case.

---

## Package structure

```
backend/
├── notebooks/                          # Workshop notebooks (one per feature track)
│   ├── feature0_baseline_rag.ipynb
│   ├── ...
│   └── ...
└── src/sme_kt_zh_collaboration_rag/
    ├── feature0_baseline_rag.py        # Runnable baseline
    ├── ...
    └── ...
```

---

## Feature tracks

### Feature 0: Baseline RAG Pipeline (`feature0_baseline_rag.ipynb`)

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

## Further feature tracks

Features 1–4 (Evaluation, Structured Outputs, Query Intelligence, Agent Workflows) will be detailed here soon.

---

## LLM backends

| Backend | Environment variable | Default model |
|---------|---------------------|---------------|
| `ollama` (default) | — | `mistral-nemo:12b` |
| `openai` | `OPENAI_API_KEY` | `gpt-4o-mini` |

Set `BACKEND=<name>` and optionally `MODEL=<model-name>` as environment variables before running any feature module.
