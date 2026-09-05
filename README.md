TRACK_ID=PS02

# ClaimLens — Motor Insurance Claims Evidence Review Assistant

> **Track:** Insurance  
> **Track ID:** PS02  
> **Validation Key:** PS02  
> **Target Audience:** Motor Claims Investigators (Two-Wheelers & Cars)

---

## 📌 Executive Summary

**ClaimLens** is an evidence-grounded AI assistant built specifically for motor insurance claims investigators. In motor insurance, claims investigators spend hours comparing disjointed claim forms, FIR reports, repair estimates, and incident narratives against complex policy wordings that frequently conflict with one another.

ClaimLens solves this by:
1. **Extracting & Structuring Evidence** from claim forms, repair estimates, FIRs, and incident narratives.
2. **Executing Deterministic Verification** (reporting windows, numeric limits, document presence, IDV calculations) in pure Python.
3. **Retrieving Policy Rules via Local RAG** using Gemini embeddings (`gemini-embedding-001`) with zero external network vector DBs.
4. **Detecting Cross-Document Contradictions** (date discrepancies, amount mismatches, vehicle mismatches, theft vs accident conflicts) without smoothing them over.
5. **Synthesizing Evidence-Grounded Recommendations** (`APPROVE`, `REJECT`, `REQUEST INFORMATION`) via Gemini with mandatory clause and document citations.
6. **Escalating Uncertain Cases** to human investigators whenever evidence is conflicting, incomplete, or ambiguous.

---

## 🚀 Quick Start (Judge / Evaluator Instructions)

### Prerequisites
- Python 3.11 (or 3.10+)
- A Gemini API Key (`GEMINI_API_KEY`)

### 1-Step Application Launch
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set your Gemini API key (Windows PowerShell)
$env:GEMINI_API_KEY="your_actual_gemini_api_key"

# (Linux / macOS)
# export GEMINI_API_KEY="your_actual_gemini_api_key"

# 3. Run the application
python app.py
```
Open **`http://localhost:8000`** in your browser to access the complete interactive Claims Review Assistant dashboard.

---

## 🏗️ Architecture & Technical Design

```
                     ┌─────────────────────────────────────────┐
                     │          Claims Investigator UI          │
                     └────────────────────┬────────────────────┘
                                          │
                                          ▼
                     ┌─────────────────────────────────────────┐
                     │          FastAPI Server (app.py)        │
                     └────────────────────┬────────────────────┘
                                          │
                                          ▼
                     ┌─────────────────────────────────────────┐
                     │       Evidence Extraction Engine        │
                     └────────────────────┬────────────────────┘
                                          │
                  ┌───────────────────────┴───────────────────────┐
                  ▼                                               ▼
    ┌───────────────────────────┐                   ┌───────────────────────────┐
    │  Deterministic Rule Engine│                   │   Local Policy RAG System │
    │   (Python Rule Logic)     │                   │  (Gemini Embeddings + DB) │
    └─────────────┬─────────────┘                   └─────────────┬─────────────┘
                  │                                               │
                  └───────────────────────┬───────────────────────┘
                                          ▼
                     ┌─────────────────────────────────────────┐
                     │       Contradiction Engine              │
                     │  (Cross-Document Field Matching)        │
                     └────────────────────┬────────────────────┘
                                          │
                                          ▼
                     ┌─────────────────────────────────────────┐
                     │       GenAI Reasoner Engine             │
                     │    (Gemini Structured Output)           │
                     └────────────────────┬────────────────────┘
                                          │
                                          ▼
                     ┌─────────────────────────────────────────┐
                     │     Evidence & Citation Validator       │
                     │  (APPROVE / REJECT / REQUEST INFO /     │
                     │          HUMAN ESCALATION)              │
                     └─────────────────────────────────────────┘
```

---

## 🔑 Key Engineering Principles

1. **Clear Separation of Logic:** Deterministic calculations (dates, amounts, thresholds, required fields) are processed in pure Python modules. Language interpretation, semantic mapping, and summary generation are delegated to Gemini.
2. **Grounding & Traceable Citations:** Every finding cites the specific document source (e.g., `Claim Form -> incident_date`) and policy clause ID (e.g., `POLICY-05`).
3. **No Smooth Over / Anti-Hallucination:** Contradictions between documents are surfaced directly. The AI is strictly instructed to flag missing or conflicting information rather than inventing facts or making assumptions.
4. **Local Network Privacy:** Vector search and storage are completely local. Only direct calls to the Gemini API occur over the network.

---

## 📁 Repository Structure

```
ClaimLens/
├── app.py                     # Single-command FastAPI application server
├── requirements.txt           # Minimal python dependencies
├── README.md                  # Project documentation (TRACK_ID=PS02)
├── .env.example               # Environment template
├── .gitignore                 # Excludes private/temp files (including MASTER_PROMPT.md)
│
├── src/                       # Core Python package
│   ├── config.py              # Configuration & env management
│   ├── schemas.py             # Pydantic data models for claims, evidence, and results
│   ├── rule_engine.py         # Deterministic rule engine (Python logic)
│   ├── policy_rag.py          # Local vector retrieval for motor policy clauses
│   ├── contradiction_engine.py# Cross-document consistency & contradiction analyzer
│   ├── genai_reasoner.py      # Gemini integration with structured schema validation
│   └── pipeline.py            # End-to-end evidence review orchestrator
│
├── prompts/                   # System & reasoning prompts
│   ├── claim_extraction.py    # Claim field extraction prompt
│   ├── policy_reasoning.py    # Grounded reasoning prompt
│   └── contradiction_prompt.py# Contradiction analysis prompt
│
├── data/                      # System-owned policy & demo claims data
│   ├── policy/                # Fictional Motor Insurance Policy (POLICY-01 to POLICY-08)
│   └── claims/                # 5 Test cases (Approvable, Contradiction, Missing Doc, Exclusion, Uncertain)
│
├── frontend/                  # Web dashboard served directly by app.py
│   ├── index.html             # Investigator interface HTML
│   ├── style.css              # Glassmorphism & dark-mode styling
│   └── app.js                 # Dashboard dynamic interaction logic
│
└── tests/                     # Automated test suite
    ├── test_rule_engine.py    # Unit tests for deterministic logic
    ├── test_contradictions.py # Unit tests for contradiction detection
    └── test_pipeline.py       # Integration tests
```

---

## 🧪 Test Cases Included

- **Case 1 (Normal / Approvable):** All documents present, dates consistent, claim within 7-day reporting window, covered accident -> `APPROVE`.
- **Case 2 (Contradiction / Request Info):** Claim form incident date conflicts with Repair Estimate date -> `REQUEST INFORMATION` + Flagged Contradiction.
- **Case 3 (Missing Document):** Theft claim without required FIR document -> `REQUEST INFORMATION` + Cites `POLICY-06`.
- **Case 4 (Exclusion / Rejection):** Claim description indicates vehicle used for commercial racing / drunk driving -> `REJECT` + Cites `POLICY-04`.
- **Case 5 (Uncertain Case):** Ambiguous description with unverified damages -> `ESCALATE TO HUMAN INVESTIGATOR`.

---

## 📜 License
Developed for NexusTiQ24 GenAI Hackathon (PS02 Track).
