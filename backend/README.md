# Backend RAG Pipeline

This package (`sme_kt_zh_collaboration_rag`) contains the notebooks and the supporting Python modules that run the RAG pipeline for the PrimePack AG
sustainability use case.

---

## Package structure

```
backend/
├── notebooks/                              # Workshop notebooks (one or more per feature track)
│   ├── feature0a_baseline_rag.ipynb        # Baseline RAG pipeline
│   ├── feature0b_ingestion.ipynb           # Document ingestion and chunking deep-dive
│   ├── feature1a_evaluation.ipynb          # RAGAS evaluation (Faithfulness, AnswerRelevancy, ContextPrecision, ContextRecall)
│   ├── feature1b_dataset_creation.ipynb    # Synthetic Q&A dataset generation
│   ├── feature2a_structured_outputs.ipynb  # Structured JSON outputs with evidence levels
│   ├── feature3a_advanced_retrieval.ipynb  # BM25, hybrid retrieval, metadata filtering
│   ├── feature3b_conversation.ipynb        # Multi-turn conversation management
│   ├── feature3c_query_techniques.ipynb    # Query expansion and HyDE
│   ├── feature3d_context_enrichment.ipynb  # Neighbouring-chunk context expansion
│   └── feature4a_tools.ipynb – feature4e_rag_subagent.ipynb  # Tools and agent workflows
└── src/sme_kt_zh_collaboration_rag/
    ├── feature0_baseline_rag.py        # Five-step RAG pipeline (chunking, embedding, retrieval, generation)
    ├── feature0_ingestion.py           # Parser comparison, chunking utilities, token analysis
    ├── feature1_evaluation.py          # Shared EVALUATION_QUERIES with ground-truth answers
    ├── feature3_advanced_retrieval.py  # BM25, hybrid, metadata-filter retrieval
    └── main.py                         # FastAPI server entry point (controller + frontend)
```

---

## Feature tracks

### Feature 0a: Baseline RAG Pipeline (`feature0a_baseline_rag.ipynb`)

Introduces the five-stage RAG loop and demonstrates it end-to-end against the PrimePack AG corpus.

| Step | Function               | What it does                                                                |
|------|------------------------|-----------------------------------------------------------------------------|
| 1    | `load_chunks()`        | Load all documents from `data/` and split into chunks (skips files > 20 MB) |
| 2    | `build_vector_store()` | Embed chunks and persist to ChromaDB                                        |
| 3    | `inspect_retrieval()`  | Run a semantic search and print ranked results                              |
| 4    | `build_agent()`        | Assemble the RAG agent from the retriever and an LLM backend                |
| 5    | `ask()`                | Send a query and stream the grounded answer                                 |

### Feature 0b: Document Ingestion (`feature0b_ingestion.ipynb`)

Deep-dive into document parsing and chunking — separate from the baseline so the ingestion workflow can be explored independently.

- PDF parser comparison: markitdown vs. docling
- Chunking strategies: fixed-size, header-based, paragraph-aware
- Token limit: embedding model truncates at 256 tokens
- Retrieval impact of chunking strategy choices

### Feature 1a: Evaluation (`feature1a_evaluation.ipynb`)

Systematic measurement of RAG pipeline quality using RAGAS.

- Part 1 (reference-free): Faithfulness and AnswerRelevancy
- Part 2 (ground truth): ContextPrecision and ContextRecall
- Shared queries defined in `feature1_evaluation.py`

### Feature 1b: Dataset Creation (`feature1b_dataset_creation.ipynb`)

Scaling the evaluation dataset beyond manual queries.

- Manual "golden query" reference set
- Synthetic Q&A generation from vector store chunks via LLM

### Feature 2a: Structured Outputs (`feature2a_structured_outputs.ipynb`)

Making claim quality machine-readable.

- Three prompting approaches: baseline prose, entity-grounding, JSON mode
- Pydantic validation layer for output reliability
- Evidence levels: VERIFIED / CLAIMED / MISSING / MIXED

### Feature 3a: Advanced Retrieval (`feature3a_advanced_retrieval.ipynb`)

Four retrieval strategies compared side-by-side.

- Baseline semantic search
- BM25 (exact keyword matching)
- Hybrid (semantic + BM25 via Reciprocal Rank Fusion)
- Metadata filtering (scope search to known documents)

### Feature 3b–3c: Conversation and Query Techniques

- `feature3b`: Multi-turn conversation management with history
- `feature3c`: Query expansion and HyDE for better semantic retrieval

### Feature 3d: Context Enrichment (`feature3d_context_enrichment.ipynb`)

Handling answers that span chunk boundaries.

- Fixed-size chunking with `chunk_index` metadata
- ContextWindowRetriever: expand retrieved chunks with their neighbours
- Token budget analysis for window sizes 0, 1, 2

### Feature 4a–4e: Tools and Agents

Multi-step agent patterns for complex queries.

- `feature4a`: LLM tool use fundamentals
- `feature4b`: LLM agents
- `feature4c`: RAG as a tool
- `feature4d`: RAG agent
- `feature4e`: RAG subagent for parallel multi-document queries

---

## Running the backend server

`main.py` starts a FastAPI server that wires together the RAG agent and in-memory conversation databases:

```bash
# From the project root
cd backend
BACKEND=openai python -m sme_kt_zh_collaboration_rag.main

# Or with uvicorn for hot reload during development
uvicorn sme_kt_zh_collaboration_rag.main:app --reload --port 8080
```

The server starts at `http://localhost:8080`. The frontend (in `frontend/`) connects to it automatically.

---

## Running the pipeline from the command line

```bash
# Default (OpenAI)
python -m sme_kt_zh_collaboration_rag.feature0_baseline_rag

# Ollama backend
BACKEND=ollama python -m sme_kt_zh_collaboration_rag.feature0_baseline_rag

# Custom query
QUERY="Which tape products have a verified EPD?" \
python -m sme_kt_zh_collaboration_rag.feature0_baseline_rag

# Force rebuild of the vector store
RESET_VS=1 python -m sme_kt_zh_collaboration_rag.feature0_baseline_rag

# Override model
MODEL=gpt-4o BACKEND=openai python -m sme_kt_zh_collaboration_rag.feature0_baseline_rag
```

The vector store is written to `backend/data_vs.db`. On subsequent runs, re-embedding is skipped if the store already exists (`RESET_VS=1` forces a rebuild).

---

## LLM backends

| Backend  | Environment variable | Default model      |
|----------|----------------------|--------------------|
| `openai` | `OPENAI_API_KEY`     | `gpt-4o-mini`      |
| `ollama` | —                    | `mistral-nemo:12b` |

Set `BACKEND=<name>` and optionally `MODEL=<model-name>` as environment variables before running any feature module.
