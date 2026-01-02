Use a dual-store “Table RAG” pattern: keep CSV tables in a structured query store (SQLite/DuckDB) for exact cell retrieval + calculations, and also index table metadata + row snippets in your existing vector DB so the system can find the right table semantically.

This scales well to ~230 tables and plugs cleanly into your 3 existing RAG systems.

1) Store architecture (recommended)
A) Vector DB (Chroma) — “table discovery”
Create a new collection (or add to existing with doc_type="table"):

One document per table (table-level card)
Contains: title/caption, purpose, column headers, units, applicability notes, source reference.
Embedding works well for “Which table applies?” questions.

Optional: one document per row (row-level snippets)
Good when users ask “what is the factor for X?” and X is a row label.
Keep row docs short and structured (e.g., JSON-like text).

Metadata to include in Chroma (critical):

doc_type: "table_card" or "table_row"
table_id: stable ID (e.g., NFPA70_2023_T220.12)
domain: matches your router domains (NFPA/UFC/etc.)
source_title, rev, section_path (if applicable), table_number, caption
units
csv_path (or table_store_key)
B) Relational store (SQLite or DuckDB) — “exact cell lookup + math”
Load all CSVs into a single DB file:

tables (metadata registry)
table_<table_id> actual data tables or a normalized “long format” table
Two common layouts:

Option 1 (simpler): one SQL table per CSV

Pros: easy import, mirrors the CSV
Cons: dynamic querying across many tables is slightly harder
Option 2 (scales best): normalized “long” format
Single table like:

table_cells(table_id, row_key, col_key, value, value_num, unit, notes, row_order, col_order) Plus:
table_rows(table_id, row_key, row_label, ...)
table_cols(table_id, col_key, col_label, ...)
This makes it easy to query any table uniformly and lets you do robust matching.

2) Ingestion pipeline (CSV → Vector + SQL)
Step 1: Standardize each CSV
For each CSV:

Ensure header row is clean
Add (or infer) units
Identify “row label” column (often first column)
Save table metadata in tables registry:
table_id, caption, domain, source, edition/rev, notes, units, primary_keys, etc.
Step 2: Load into SQL
Use DuckDB (very fast for CSV import) or SQLite.
Normalize numeric columns (value_num) where possible to support calculations.
Step 3: Create vector “table cards”
For each table produce a text block like:

Table: {table_number} — {caption}
Domain: {domain}, Source: {source_title} (rev {rev})
Use-case: {short description}
Columns: {col1, col2, …}
Rows: {row label examples}
Units: {units}
Notes: {applicability}
Embed that into Chroma with metadata.

Step 4 (optional but helpful): Create vector “row snippets”
For each row, embed something like:

Table {table_id} row: {row_label}
{col1}: {val1}; {col2}: {val2}; …
Units/notes…
This improves retrieval when the row label is semantically described.

3) Runtime query flow (how it works with your 3 RAG systems)
Add a Tool Router after your domain router:

Detect domain (you already planned this)
Detect intent:
text_lookup (books)
table_lookup (CSV tables)
calc (often requires both)
Retrieval logic
If table_lookup or calc:

Query Chroma for doc_type="table_card" (+ maybe "table_row") filtered by domain/rev.
Pick best table_id.
Execute a SQL query against DuckDB/SQLite to fetch:
matching row(s)/column(s)
plus “nearby” rows if needed (for ranges)
Return:
the exact value(s)
table citation (table_id + caption + source + rev)
If the question needs rules + a table (common for calculations):

Retrieve rules from your book RAG and retrieve the referenced table from the table store.
Compute deterministically.
Why this beats “CSV as plain text chunks”
Vector-only CSV ingestion is weak for exact values.
SQL gives exactness and reproducibility (important for “demand calculation requirements and do the calculation”).
4) Citation / auditability
Treat a table lookup like a citable source:

Citation format: {source_title} {rev}, Table {table_number} (“{caption}”), row={row_label}, col={col_label}
Store these fields in tables metadata so the assistant can cite consistently.
5) Minimal implementation checklist
New scripts/modules
execution/ingest_tables.py

Reads CSV folder + a tables_manifest.csv/json (caption, domain, rev, etc.)
Loads into DuckDB/SQLite
Creates Chroma docs for table cards (+ optional row docs)
execution/table_tools.py

find_relevant_tables(query, domain, rev) -> [table_id] (via Chroma)
lookup_table_value(table_id, row_match, col_match, filters) -> result
get_table_excerpt(table_id, row_keys, col_keys) for “show your work”
Changes to rag_agent.py
Add tool router:
if query mentions “Table …” or looks like a factor/value request → table tool
else normal book RAG
hybrid for calculations
6) Practical tip: manage the 230 tables with a manifest
Create tables_manifest.csv with columns like:

table_id, domain, source_title, rev, table_number, caption, units, row_label_col, notes, tags
This keeps ingestion consistent and makes routing accurate.

If you tell me (a) what your vector DB is (still Chroma?), (b) whether you can add DuckDB, and (c) whether the tables are tied to specific books/editions, I can propose the exact folder layout + schema + example code stubs for ingest_tables.py and table_tools.py.