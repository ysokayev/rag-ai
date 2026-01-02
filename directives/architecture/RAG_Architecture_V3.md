# RAG System Architecture (V3)

## Executive Summary
The Agentic Code RAG System (V3) is a high-precision compliance assistant designed to retrieve, reason about, and calculate requirements from technical standards (NFPA, UFC, FGI/FBC). 

**Key Differentiator:** It separates **Normative Requirements** (cited text) from **Guidance/Calculations** (deterministic derivation) to prevent hallucination.

## Core Components

### 1. Data Architecture
*   **Storage:** ChromaDB (Local Persistent).
*   **Index Strategy:** Parent-Child Chunking.
    *   *Parent:* Large context window (~2000 tokens) for answer synthesis.
    *   *Child:* Small overlapping chunks (~400 tokens) for dense vector retrieval.
*   **Metadata Schema:**
    *   `source`, `source_title`, `rev` (Edition).
    *   `chunk_role`: `normative` vs `table`.
    *   `contains_formula`: Boolean flag for calculation prioritization.

### 2. Retrieval Implementation (`rag_agent.py`)
*   **Router:**
    *   **Domain:** Routes to specific collections (`rag_code_only`, `rag_healthcare`, `rag_military`).
    *   **Intent:** Distinguishes `lookup` (text search) from `calc` (demand calculations).
*   **Ranking (Collapsed Parent Score):**
    `Score = 0.55 * Max(Child) + 0.35 * Norm(Sum_Top5) + 0.10 * Norm(Count)`
    *   Prioritizes parents with *strong* matches over parents with *many weak* matches.

### 3. Dynamic Calculation Layer (`calc_tools.py`)
A deterministic "Safe Math Engine" that replaces LLM arithmetic.
*   **Mechanism:** `Intent=Calc` -> Extract Formula & Vars -> Tool Call (`perform_calculation`) -> `simpleeval` Execution.
*   **Safety:** No `eval()`. Standardized unit stripping (VA, ft, A).
*   **Traceability:** Outputs explicitly cite the formula source rule.

### 4. Output Protocol (Two-Channel)
The System Prompt enforces a strict separation:
1.  **Normative Answer (Cited Only):**
    *   Must cite Source/Section for every claim.
    *   NO derived numbers, only raw requirements.
2.  **Guidance (Non-Citable):**
    *   Calculation steps and results.
    *   Practical application advice.
    *   User assumptions labeled.

## Usage
**Ingestion:**
```bash
python execution/ingest_books.py --domain code --reset
```

**Run Agent:**
```bash
python execution/rag_agent.py --domain code
```

## Future Roadmap: Table RAG
Implementation of `methodfortables.md` is upcoming.
*   **Goal:** Exact cell lookup for 230+ tables.
*   **Architecture:** Hybrid Vector (for discovery) + SQL/DuckDB (for exact cell values).
*   **Integration:** Will add `table_lookup` intent to the existing Router.
