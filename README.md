# Mamaearth Returns & Growth Intelligence Pipeline

My capstone project. I took Mamaearth order data and worked on it in three steps: SQL reports first, then cleaning and analysis in pandas, and finally a short written summary generated with Gemini.

## What I found

- COD orders get returned the most, 44.4% of the time. UPI is at 18.9% and Card at 14.7%.
- The worst group is COD orders from Tier-2 cities, where 54.5% come back.
- Revenue after cleaning is Rs 97,358.30. The raw number was Rs 99,860.20, and the Rs 2,501.90 difference is exactly the 5 duplicate orders.
- January looks like the best month, but that is because of two very large orders. Without them March is the real peak (Rs 20,318.90).

## Folders

- `sql/` - schema, seed data and the reports (a to i)
- `data/` - the 3 raw CSV files, I never edited these
- `analysis/` - `clean_and_eda.py` and `visualize.py`
- `visualizations/` - the 2 charts
- `narrator/` - `findings.json`, `generate_narrative.py` and `sample_output.txt`

## About the data

The CSVs are messy on purpose. Payment method is written 7 different ways (upi, UPI, Card, card and so on), 5 orders are duplicates, and some discount and rating values are missing. The SQL part uses the data as it is, and all the cleaning happens in pandas.

## Setup

    pip install pandas matplotlib google-genai

You also need sqlite3 for the SQL part.

## How to run

### 1. SQL

Run these from the main project folder:

    sqlite3 mamaearth.db ".read sql/schema.sql"
    sqlite3 mamaearth.db ".read sql/seed_data.sql"
    sqlite3 mamaearth.db ".read sql/reports.sql"

You should get 45 customers, 16 products and 180 orders. If you want to run it again, start from schema.sql, because it drops and recreates the tables.

### 2. Analysis

The Python scripts read the CSV files from the folder you run them in. So first copy the 3 files from `data/` (customers.csv, products.csv, orders.csv) into the main project folder, then run:

    python analysis/clean_and_eda.py
    python analysis/visualize.py

The first script prints all the results and writes `narrator/findings.json` at the end. The second one saves the charts into `visualizations/`. This part doesn't need the SQL step.

### 3. Narrator

This one needs `narrator/findings.json` from step 2, so run that first. The script is written for Google Colab and reads the key from Colab secrets. To use Gemini, get a free key from https://aistudio.google.com/apikey and add it in Colab as a secret named `GEMINI_API_KEY`. Then run:

    python narrator/generate_narrative.py

If the Gemini call fails, it falls back to a simple built-in template, so the script still gives an answer. The output I got from Gemini is saved in `narrator/sample_output.txt`.

## How the pieces connect

The raw CSVs go into SQL for the reports. The same CSVs also go through pandas cleaning, which produces `findings.json`, and the narrator reads that file.

The two revenue totals match up: SQL raw 99,860.20 minus pandas cleaned 97,358.30 is 2,501.90, which is the 5 duplicate orders.
