# SME-KT-ZH Collaboration — Sustainability RAG

A collaborative prototyping project building an open-source RAG (Retrieval-Augmented Generation) backbone that SMEs can adapt for their own sustainability knowledge management.

## Scenario

**PrimePack AG** sells packaging products (pallets, cardboard boxes, tape) sourced from multiple suppliers. Sustainability claims are increasingly important, from customers requiring CSRD-compliant data to procurement needing to evaluate supplier evidence quality.

The core challenge: sustainability information is spread across many documents (EPDs, supplier brochures, company reports, regulatory frameworks), claims have widely varying evidence quality, and employees must answer questions like:
- *"What does Supplier A claim for Product X, and can we trust it?"*
- *"Which suppliers are compliant with our EPD requirement?"*
- *"Can we tell a customer that this tape is PFAS-free?"*
- *"Which evidence is missing before we can respond?"*

The RAG assistant should **cite sources explicitly**, **separate facts from claims**, **highlight gaps and conflicts**, and **refuse to conclude when evidence is insufficient**.

---

## Installation

```bash
# Create and activate a virtual environment
python -m venv rag_venv
source rag_venv/bin/activate  # on Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

The `conversational_toolkit` and `backend` packages are installed automatically via `requirements.txt`. If needed, install them manually:

```bash
pip install -e conversational-toolkit/
pip install -e backend/
```

### Ollama (local LLM)

```bash
# Start the Ollama server
ollama serve

# Download a model, e.g. mistral-nemo:12b
ollama pull mistral-nemo:12b
```

### Renku environment

```bash
# Start Ollama pointing to the mounted model directory
OLLAMA_MODELS=$RENKU_MOUNT_DIR/ollama_models ollama serve

# List available models
ollama list

# Download a model
ollama pull mistral-nemo:12b
```

---

## Quick Start

```bash
# Run the full pipeline with default Ollama backend
python -m sme_kt_zh_collaboration_rag.baseline_rag

# Use OpenAI instead
BACKEND=openai python -m sme_kt_zh_collaboration_rag.baseline_rag

# Custom query
QUERY="Which tape products have a verified EPD?" python -m sme_kt_zh_collaboration_rag.baseline_rag

# Force rebuild of the vector store
RESET_VS=1 python -m sme_kt_zh_collaboration_rag.baseline_rag
```

---

## Repository Structure

```
.
├── backend/                   # RAG pipeline application
│   ├── notebooks/             # Workshop notebooks (feature0 – feature5)
│   └── src/sme_kt_zh_collaboration_rag/
│       ├── feature0_baseline_rag.py    # Five-step pipeline (chunking → embedding → retrieval → generation)
│       ├── feature1_ingestion.py
│       └──
│
├── conversational-toolkit/    # Reusable RAG components (toolkit library)
│   └── src/conversational_toolkit/
│       ├── agents/            # RAG agent (retrieval + generation)
│       ├── chunking/          # PDF, Excel, Markdown chunkers
│       ├── embeddings/        # Sentence Transformer embeddings
│       ├── llms/              # OpenAI, Ollama, local LLM backends
│       ├── retriever/         # Vector store retriever, BM25, hybrid
│       ├── utils/             # Prompt building, query expansion, RRF
│       └── vectorstores/      # ChromaDB vector store
│
├── data/                      # Document corpus (see below)
│
└── frontend/                  # (in development)
```

---

## Dataset

All documents are in `data/`. The file prefix defines the document type:

| Prefix | Meaning |
|--------|---------|
| `ART_` | Artificial workshop scenario document |
| `EPD_` | Verified, third-party Environmental Product Declaration |
| `SPEC_` | Product specification, datasheet, or article document |
| `REF_` | Regulatory or reference document |
| `EVALUATION_` | Evaluation / ground-truth dataset (not part of the RAG corpus) |

---

### Artificial Documents (`ART_`)

Designed with deliberate flaws to demonstrate RAG failure modes.

| File | Type | What it demonstrates |
|------|------|---------------------|
| `ART_product_catalog.md` | Internal policy | Portfolio scope, evidence-level policy, customer communication rules, open action items. The machine-readable product table lives in `product_overview.xlsx`. |
| `ART_internal_procurement_policy.md` | Internal policy | Evidence levels (A–D), EPD requirements, PFAS policy |
| `ART_supplier_brochure_tesa_ECO.md` | Supplier marketing | **Unverified claim** — 68% CO₂ reduction, no EPD |
| `ART_supplier_brochure_CPR_wood_pallet.md` | Supplier marketing | **Unverified LCA figures**; FSC claim without certificate |
| `ART_logylight_incomplete_datasheet.md` | Supplier datasheet | **Missing data** — all LCA fields "not yet available" |
| `ART_relicyc_logypal1_old_datasheet_2021.md` | Superseded document | **Temporal conflict** — 2021 figure vs. 2023 verified EPD |
| `ART_customer_inquiry_frische_felder.md` | Customer communication | CSRD request with open [ACTION] items |

---

### Environmental Product Declarations (`EPD_`)

Third-party verified EPDs. Naming: `EPD_{category}_{supplier}_{product}.pdf`

**Pallets:**

| File | Supplier | Product (ID) |
|------|----------|--------------|
| `EPD_pallet_CPR_noe.pdf` | CPR System | Noé Pallet (32-100) |
| `EPD_pallet_relicyc_logypal1.pdf` | Relicyc | Logypal 1 (32-103) — 2023 |
| `EPD_pallet_stabilplastik_ep08.pdf` | StabilPlastik | EP 08 (32-105) |

**Cardboard Boxes:**

| File | Supplier | Product (ID) |
|------|----------|--------------|
| `EPD_cardboard_redbox_cartonpallet.pdf` | Redbox | Cartonpallet CMP (11-100) |
| `EPD_cardboard_grupak_corrugated.pdf` | Grupak | Corrugated cardboard (11-101) |

**Tape:**

| File | Supplier | Product (ID) |
|------|----------|--------------|
| `EPD_tape_IPG_hotmelt.pdf` | IPG | Hot Melt Tape (50-100) |
| `EPD_tape_IPG_wateractivated.pdf` | IPG | Water-Activated Tape (50-101) |

---

### Product Specifications & Datasheets (`SPEC_`)

Supplier-provided specs, datasheets, and article documents. Naming: `SPEC_{category}_{supplier}_{product}.pdf`

**Pallets:**

| File | Supplier | Product |
|------|----------|---------|
| `SPEC_pallet_CPR_plastic.pdf` | CPR System | Plastic Pallet (32-102) |
| `SPEC_pallet_CPR_wood.pdf` | CPR System | Wooden Pallet (32-101) |
| `SPEC_pallet_CPR_recycled_plastic.pdf` | CPR System | Recycled plastic pallet PR12 |
| `SPEC_pallet_relicyc_logypal1.pdf` | Relicyc | Logypal 1 — product info |
| `SPEC_pallet_relicyc_1208MR.pdf` | Relicyc | Pallet 1208MR |
| `SPEC_pallet_stabilplastik_ep08.pdf` | StabilPlastik | EP 08 — datasheet |

**Tape:**

| File | Supplier | Product |
|------|----------|---------|
| `SPEC_tape_CST_synthetic_rubber.pdf` | CST | Synthetic rubber tape |
| `SPEC_tape_WAT_central_brand.pdf` | WAT | WAT tape — article document |
| `SPEC_tape_WAT_260.pdf` | WAT | WAT 260 — technical data sheet |
| `SPEC_tape_tesa_tesapack58297.pdf` | Tesa | tesapack 58297 (German) |
| `SPEC_tape_tesa_sustainability_report_2024.pdf` | Tesa | Company sustainability report 2024 (German) |

**Master data:**

| File | Content |
|------|---------|
| `product_overview.xlsx` | Machine-readable product table: all 12 products with IDs, suppliers, categories, and EPD status. Referenced by `ART_product_catalog.md` for the full product list. |

---

### Reference & Regulatory Documents (`REF_`)

| File | Content |
|------|---------|
| `REF_ghg_protocol_product_lca.pdf` | GHG Protocol — Product LCA standard |
| `REF_ghg_protocol_corporate_value_chain.pdf` | GHG Protocol — Scope 3 / value chain |
| `REF_ghg_protocol_corporate_standard.pdf` | GHG Protocol — revised corporate standard |
| `REF_eu_csrd.pdf` | EU Corporate Sustainability Reporting Directive (CSRD) |
| `REF_eu_climate_reporting_guidelines.pdf` | EU guidelines on climate-related reporting |
| `REF_ch_eu_sustainability_obligations.pdf` | Swiss/EU sustainability obligations |
| `REF_iso14024_conformance_statement.pdf` | ISO 14024 conformance statement |
| `REF_ecologo_catalogue.pdf` | ecoLogo certification catalogue |

---

### Evaluation Document

| File | Content |
|------|---------|
| `EVALUATION_qa_ground_truth.md` | Sample questions with expected answers, required sources, and difficulty ratings. Use to manually verify RAG output. Not included in the RAG corpus. |

---

## Key Design Decisions in the Dataset

**Evidence quality varies deliberately.** Products span verified EPDs (Level A) to missing data (Level D). The RAG must distinguish these — not just retrieve numbers.

**Conflicts are intentional.** `ART_relicyc_logypal1_old_datasheet_2021.md` and `EPD_pallet_relicyc_logypal1.pdf` contain different GWP figures. The RAG should flag the conflict and prefer the more recent, verified source.

**Gaps are part of the answer.** For the LogyLight pallet and PFAS declarations, the correct answer is "we don't have this data." A RAG that fabricates an answer here fails.

**The portfolio boundary matters.** The product catalog defines which products exist. Queries about products outside the catalog (e.g., "Lara Pallet") should be answered as "not in our portfolio."

---

## LLM Backends

| Backend | Command | Notes |
|---------|---------|-------|
| Ollama (default) | `python -m sme_kt_zh_collaboration_rag.baseline_rag` | Requires `ollama serve` and `ollama pull mistral-nemo:12b` |
| OpenAI | `BACKEND=openai python -m ...` | Requires `OPENAI_API_KEY` env variable |
| SDSC Qwen | `BACKEND=qwen python -m ...` | Requires `SDSC_QWEN3_32B_AWQ` env variable |

Override the model: `MODEL=gpt-4o BACKEND=openai python -m ...`

---

## Development

```bash
# Run pre-commit hooks
pre-commit install
pre-commit run --all-files

# Run tests
pytest
```
