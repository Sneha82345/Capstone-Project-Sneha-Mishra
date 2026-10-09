# Mamaearth Returns & Growth Intelligence Pipeline

SQL layer → pandas analysis layer → GenAI narrative layer.

## Repo structure
sql/ (schema, seed, reports) · data/ (3 raw CSVs, never edited) · analysis/ (clean_and_eda.py, visualize.py) ·
visualizations/ (2 PNGs) · narrator/ (findings.json, generate_narrative.py, sample_output.txt)

## Setup
pip install pandas matplotlib google-genai

## Run order (from the repo root)

### 1. SQL layer
sqlite3 mamaearth.db < sql/schema.sql
sqlite3 mamaearth.db < sql/seed_data.sql   # loads CSVs, converts blanks to NULL
sqlite3 mamaearth.db < sql/reports.sql     # reports a–i
Expected counts: 45 customers, 16 products, 180 orders. To re-run, start again from schema.sql.

### 2. Analysis layer (independent of SQL, reads the raw CSVs)
python analysis/clean_and_eda.py   # prints all results; Task 5 reconciles to the SQL total;
                                   # its final step WRITES narrator/findings.json
python analysis/visualize.py       # writes visualizations/*.png

### 3. Narrator layer
python narrator/generate_narrative.py
- No API key: runs the offline template path (no network needed).
- With Gemini: get a free key at https://aistudio.google.com/apikey, then
  export GEMINI_API_KEY="your_key"   (PowerShell: $env:GEMINI_API_KEY="your_key")
  and run the same command. The saved online output is in narrator/sample_output.txt.

## Data flow
raw CSVs → SQL (Part 1, reports) 
raw CSVs → pandas cleaning (Part 2) → findings.json → narrator (Part 3).
Reconciliation: SQL raw revenue 99,860.20 − pandas cleaned 97,358.30 = 2,501.90 = the 5 duplicate orders.
