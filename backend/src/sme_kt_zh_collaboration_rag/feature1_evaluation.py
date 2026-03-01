"""
Feature Track 1: Evaluation & Validation

Canonical test set for the PrimePack AG RAG system.
Import EVALUATION_QUERIES to run the evaluation suite against any pipeline variant.
"""

EVALUATION_QUERIES: list[dict] = [
    # portfolio scope
    {
        "query": "Does PrimePack AG offer a product called the Lara Pallet?",
        "ground_truth_answer": (
            "No. The Lara Pallet does not exist in the PrimePack AG portfolio. The current pallet portfolio is: Noé Pallet (32-100, CPR System), Wooden Pallet 1208 (32-101, CPR System), Recycled Plastic Pallet (32-102, CPR System), Logypal 1 (32-103, Relicyc), LogyLight (32-104, Relicyc), and EP 08 (32-105, StabilPlastik)."
        ),
        "expected_keywords": ["not", "no", "portfolio"],
        "category": "portfolio_scope",
        "difficulty": "easy",
    },
    # multi-product retrieval
    {
        "query": "Which products in the portfolio have a third-party verified EPD?",
        "ground_truth_answer": (
            "Products with third-party verified EPDs: 50-100 (IPG Hot Melt Tape), 50-101 (IPG Water-Activated Tape), 32-100 (Noé Pallet, CPR System), 32-103 (Logypal 1, Relicyc), 32-105 (EP 08, StabilPlastik), 11-100 (Cartonpallet CMP, redbox), 11-101 (Corrugated cardboard, Grupak). Products without a verified EPD: 50-102 (tesapack ECO), 32-101, 32-102, 32-104."
        ),
        "expected_keywords": ["50-100", "50-101", "32-100", "32-103", "32-105"],
        "category": "portfolio_scope",
        "difficulty": "easy",
    },
    # claim verification
    {
        "query": "Can the 68% CO2 reduction claim for tesapack ECO (product 50-102) be included in a customer sustainability response?",
        "ground_truth_answer": (
            "No. The 68% CO2 reduction figure is a self-declared internal assessment by Tesa SE, not independently verified through an EPD. PrimePack AGs procurement policy classifies this as Level B/C evidence. It may only be cited with an explicit caveat that it is unverified. Additionally, the carbon neutrality target for end of 2025 is a forward-looking goal, not a current verified status."
        ),
        "expected_keywords": ["not", "EPD", "internal"],
        "category": "claim_verification",
        "difficulty": "hard",
    },
    # missing data
    {
        "query": "What verified environmental data is available for the LogyLight pallet (product 32-104)?",
        "ground_truth_answer": (
            "No verified environmental data is available for LogyLight (32-104). The datasheet explicitly states that GWP and all other LCA figures are not yet available. An LCA study has been commissioned (REL-LCA-2024-07) and a third-party verified EPD was expected by Q2 2025, but no verified figures exist. The 75% recycled content figure is a self-declaration with no independent audit. LogyLight must not be included in customer-facing environmental comparisons."
        ),
        "expected_keywords": ["not yet available", "LCA", "EPD"],
        "category": "missing_data",
        "difficulty": "easy",
    },
    # source conflict
    {
        "query": "Which GWP source should be used for Relicyc Logypal 1: the 2021 datasheet or the 2023 EPD?",
        "ground_truth_answer": (
            "The 2023 third-party verified EPD (Relicyc EPD No. S-P-10482) is the authoritative source. The 2021 internal datasheet reporting 4.1 kg CO2e per pallet is marked SUPERSEDED and must not be cited. When two sources conflict, PrimePack AGs policy requires preferring the more recent third-party verified source."
        ),
        "expected_keywords": ["EPD", "2023", "superseded"],
        "category": "source_conflict",
        "difficulty": "hard",
    },
    # missing data
    {
        "query": "Are any tape products confirmed to be PFAS-free?",
        "ground_truth_answer": (
            "No tape product is confirmed PFAS-free. As of January 2025, no PFAS declarations have been received from IPG or Tesa SE. The Tesa hot-melt, free of intentionally added solvents claim does not constitute a PFAS declaration. No tape product may be described as PFAS-free until explicit supplier declarations are received and reviewed."
        ),
        "expected_keywords": ["no", "not received", "declaration"],
        "category": "missing_data",
        "difficulty": "medium",
    },
    # policy
    {
        "query": "Which suppliers are not yet compliant with the EPD requirement by end of 2025?",
        "ground_truth_answer": (
            "Tesa SE (supplier of tesapack ECO, product 50-102) and CPR System (supplier of Wooden Pallet 32-101 and Recycled Plastic Pallet 32-102) are not yet compliant with the EPD requirement by end of 2025."
        ),
        "expected_keywords": ["Tesa", "CPR"],
        "category": "policy",
        "difficulty": "easy",
    },
]
