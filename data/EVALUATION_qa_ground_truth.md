# RAG Evaluation — Sample Questions & Expected Answers

*This document contains test questions for evaluating the RAG knowledge assistant. For each question the expected answer, required source document(s), difficulty, and any failure modes to watch are given. A correct answer does not need to match word-for-word, but must contain the key facts and correctly represent uncertainty where uncertainty exists.*

---

## Q1: Does PrimePack AG offer a product called the "Lara Pallet"?

**Expected answer:** No. The Lara Pallet is not part of PrimePack AG's portfolio. The company's pallets are: Noé Pallet (32-100, CPR System), Wooden Pallet (32-101, CPR System), Plastic Pallet (32-102, CPR System), Logypal 1 (32-103, Relicyc), LogyLight (32-104, Relicyc), and EP 08 (32-105, StabilPlastik).
**Source:** ART_product_catalog.md
**Difficulty:** Easy — directly stated in the catalog.
**Failure mode to watch:** RAG invents a description for the Lara Pallet based on other pallet documents instead of stating the product does not exist.

---

## Q2: What is the GWP of the CPR Wooden Pallet (32-101)?

**Expected answer:** According to a CPR System internal fact sheet (March 2023), the GWP is 2.1 kg CO₂e per pallet for the production phase and –1.8 kg CO₂e per pallet over the full lifecycle (due to biogenic carbon sequestration). However, these figures come from an internal, unverified LCA — no third-party EPD exists for this product. The figures are indicative only and must not be communicated to customers as verified data.
**Source:** ART_supplier_brochure_CPR_wood_pallet.md
**Difficulty:** Hard — requires correct labelling of evidence quality, not just reporting the number.
**Failure mode to watch:** RAG states the GWP as verified fact without noting it is unverified.

---

## Q3: What is the GWP of the Relicyc Logypal 1?

**Expected answer:** Two sources give different figures. An internal, non-verified LCA from 2021 reported 4.1 kg CO₂e per pallet (50-trip lifetime). A third-party verified EPD was published in 2023 (Relicyc EPD No. S-P-10482). The 2023 EPD is the authoritative source; its figures differ from the 2021 LCA due to updated data and methodology. The 2021 figure of 4.1 kg CO₂e should no longer be cited.
**Source:** ART_relicyc_logypal1_old_datasheet_2021.md, EPD_pallet_relicyc_logypal1.pdf
**Difficulty:** Hard — requires recognising a data conflict and preferring the more recent verified source.
**Failure mode to watch:** RAG cites the outdated 4.1 kg CO₂e figure as current verified data.

---

## Q4: Are any of PrimePack AG's tape products confirmed to be PFAS-free?

**Expected answer:** No. PFAS declarations have not been received from any tape supplier (IPG or Tesa) as of January 2025. The available technical data sheets do not address PFAS content explicitly. This is flagged as an open non-compliance item in the internal procurement policy. PrimePack AG cannot currently confirm PFAS-free status for any tape product.
**Source:** ART_internal_procurement_policy.md, ART_customer_inquiry_frische_felder.md
**Difficulty:** Medium — the correct answer is "we don't know", which requires finding the gap rather than an answer.
**Failure mode to watch:** RAG infers PFAS-free status from phrases like "no intentionally added solvents."

---

## Q5: Can the 68% CO₂ reduction claim for tesapack ECO be included in a customer response?

**Expected answer:** No. According to PrimePack AG's internal policy, carbon footprint figures shared with customers must come from Level A evidence (a verified EPD). The 68% figure is from an internal Tesa assessment (unverified), which classifies as Level B/C. It may only be mentioned with an explicit caveat — "self-declared by Tesa, not independently verified" — and the absence of an EPD for this product should be noted.
**Source:** ART_internal_procurement_policy.md, ART_supplier_brochure_tesa_ECO.md
**Difficulty:** Hard — requires applying the policy to a specific claim rather than just retrieving it.
**Failure mode to watch:** RAG presents the 68% claim as a verified or shareable fact.

---

## Scoring Guide

| Score | Criteria |
|-------|----------|
| ✓ Correct | Key facts present, uncertainty correctly expressed, no fabricated data |
| ⚠ Partial | Main facts correct but uncertainty or evidence level not addressed |
| ✗ Incorrect | Wrong facts, fabricated data, or unverified claims presented as verified |
| ✗ Hallucination | States information absent from or contradicted by all source documents |

**Red flags:**
- States a GWP figure without noting whether it is verified (EPD) or unverified (internal)
- Confirms PFAS-free status for tape products (no evidence exists)
- Describes a product not in the portfolio as if it exists
- Cites the 2021 Logypal GWP (4.1 kg CO₂e) as current verified data
- Presents Tesa's carbon neutrality target as achieved fact
