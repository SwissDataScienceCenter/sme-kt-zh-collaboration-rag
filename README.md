# SME-KT-ZH Collaboration — Sustainability RAG

A collaborative prototyping project building an open-source RAG (Retrieval-Augmented
Generation) backbone that SMEs can adapt for their own sustainability knowledge management.

## Scenario

**Andrea Packaging AG** sells packaging products (pallets, cardboard boxes, tape) sourced
from multiple suppliers. Sustainability claims are increasingly important — from customers
requiring CSRD-compliant data to procurement needing to evaluate supplier evidence quality.

The core challenge: sustainability information is spread across many documents (EPDs,
supplier brochures, company reports, regulatory frameworks), claims have widely varying
evidence quality, and employees must answer questions like:

- *"What does Supplier A claim for Product X, and can we trust it?"*
- *"Which suppliers are compliant with our EPD requirement?"*
- *"Can we tell a customer that this tape is PFAS-free?"*
- *"Which evidence is missing before we can respond?"*

The RAG assistant should **cite sources explicitly**, **separate facts from claims**,
**highlight gaps and conflicts**, and **refuse to conclude when evidence is insufficient**.

---

## Installation

```bash
# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # on Windows: venv\Scripts\activate

# Install the conversational toolkit (editable)
pip install -e conversational-toolkit/

# Install the backend
pip install -e backend/
```

### Ollama (local LLM)

```bash
# Start the Ollama server
ollama serve

# Download the default model
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
│   └── src/sme_kt_zh_collaboration_rag/
│       └── baseline_rag.py    # Five-step pipeline (chunking → embedding → retrieval → generation)
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

All documents are in `data/`. Files prefixed `ART_` are **artificial documents** created
for the workshop scenario. Files prefixed `EVALUATION_` are for RAG testing only.

### Artificial Documents (workshop scenario)

| File | Type | What it demonstrates |
|------|------|---------------------|
| `ART_product_catalog.md` | Internal reference | Authoritative product list; defines portfolio scope; use to verify "does product X exist?" queries |
| `ART_internal_procurement_policy.md` | Internal policy | Evidence levels (A–D), EPD requirements, PFAS policy, customer communication rules |
| `ART_supplier_brochure_tesa_ECO.md` | Supplier marketing | **Self-declared claims** — 68% CO₂ reduction (unverified), carbon neutrality target (not achieved); no EPD |
| `ART_supplier_brochure_CPR_wood_pallet.md` | Supplier marketing | **Internal LCA figures** passed off as environmental data; FSC claim without certificate; no EPD |
| `ART_logylight_incomplete_datasheet.md` | Supplier datasheet | **Missing data** — all LCA fields "not yet available"; self-declared recycled content only |
| `ART_relicyc_logypal1_old_datasheet_2021.md` | Superseded document | **Temporal conflict** — 2021 internal figure (4.1 kg CO₂e) vs. 2023 verified EPD; document is marked superseded |
| `ART_customer_inquiry_frische_felder.md` | Customer communication | Real customer CSRD request; internal draft response with open [ACTION] items; shows what we can/cannot answer |

### Real Supplier Documents

**Pallets:**

| File | Supplier | Product | Document type |
|------|----------|---------|---------------|
| `2_EPD_pallet_CPR.pdf` | CPR System | Noé Pallet (32-100) | EPD (verified) |
| `CPR_Rev1_ENG_PLASTIC_PALLET.pdf` | CPR System | Plastic Pallet (32-102) | Product specification |
| `CPR_Rev1_ENG_WOOD_PALLET.pdf` | CPR System | Wooden Pallet (32-101) | Product specification |
| `CPR_Rev4_Scheda-informativa-Pallet-Plastica-Riciclata-PR12_ING.pdf` | CPR System | Recycled plastic pallet | Product information |
| `3_EPD_pallet_relicyc.pdf` | Relicyc | Logypal 1 (32-103) | EPD (verified, 2023) |
| `LOGYPAL1_relicyc.pdf` | Relicyc | Logypal 1 | Product information |
| `pallet_1208MR_relicyc.pdf` | Relicyc | Pallet 1208MR | Product information |
| `4_EPD_pallet_Stabilplastik.pdf` | StabilPlastik | EP 08 (32-105) | EPD (verified) |
| `EP08-Produktovy-list-Stabilplastik-0625-EN.pdf` | StabilPlastik | EP 08 | Product data sheet |

**Cardboard Boxes:**

| File | Supplier | Product | Document type |
|------|----------|---------|---------------|
| `EPD_cardboard_box_Redbox.pdf` | Redbox | Cartonpallet CMP (11-100) | EPD (verified) |
| `EPD_cardboard_packaging_Grupak.pdf` | Grupak | Corrugated cardboard (11-101) | EPD (verified) |

**Tape:**

| File | Supplier | Product | Document type |
|------|----------|---------|---------------|
| `EPD_tape_ipg.pdf` | IPG | Hot Melt Tape (50-100) | EPD (verified) |
| `EPD_tape2_ipg.pdf` | IPG | Water-Activated Tape (50-101) | EPD (verified) |
| `Article-Document-CST-Synthetic-Rubber.pdf` | CST | Synthetic rubber tape | Article document |
| `Article-Document-WAT-Central-Brand.pdf` | WAT | WAT tape | Article document |
| `WAT_260_TDS.pdf` | WAT | WAT 260 | Technical data sheet |
| `Product information_tesapack® 58297_de-AT.pdf` | Tesa | tesapack 58297 | Product information (German) |
| `tesa_Nachhaltigkeitsbericht_2024.pdf` | Tesa | Company-level | Sustainability report 2024 (German) |

**Product Overview:**

| File | Content |
|------|---------|
| `product_overview.xlsx` | Master table: all 12 products with IDs, suppliers, EPD status |

### Reference & Regulatory Documents

| File | Content |
|------|---------|
| `1_Product-Life-Cycle-Accounting-Reporting-Standard_041613.pdf` | GHG Protocol — Product LCA standard |
| `Corporate-Value-Chain-Accounting-Reporing-Standard_041613_2.pdf` | GHG Protocol — Scope 3 / value chain |
| `ghg-protocol-revised.pdf` | GHG Protocol — revised corporate standard |
| `EU_corporate sustainability reporting.pdf` | CSRD overview |
| `EU_Guidelines on reporting climate-related information.pdf` | EU climate reporting guidance |
| `CH_bericht-entwuerfe-nachhaltigkeitspflichten-eu.pdf` | Swiss/EU sustainability obligations |
| `iso-14024-conformance-statement_final_061625-1768984660.pdf` | ISO 14024 conformance |
| `ecoLogo Catalogue_EN.pdf` | ecoLogo certification catalogue |

### Evaluation Document

| File | Content |
|------|---------|
| `EVALUATION_qa_ground_truth.md` | 16 sample questions with expected answers, required sources, and difficulty ratings. Use this to manually verify RAG output. |

---

## Key Design Decisions in the Dataset

**Evidence quality varies deliberately.** Some products have verified EPDs (Level A),
some have supplier-declared figures without independent verification (Level B/C), and some
have no data at all (Level D). The RAG must distinguish these — not just retrieve numbers.

**Conflicts are intentional.** The 2021 Relicyc datasheet and the 2023 Relicyc EPD contain
different GWP figures. The RAG should flag this and prefer the more recent, verified source.

**Gaps are part of the answer.** For the LogyLight pallet and for PFAS declarations, the
correct answer is "we don't have this data." A RAG that fabricates an answer here fails.

**The portfolio boundary matters.** The product catalog explicitly states which products
exist. Queries about products outside the catalog (e.g., "Lara Pallet") should be answered
as "not in our portfolio" — not answered using data from similar products.

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
