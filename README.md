# DATA-PIPELINE-AUTOMATION

An automated data pipeline that cleans, merges, analyzes, and reports on
messy marketing data pulled from multiple sources — CSV, JSON, Excel, and
REST APIs.

## Problem

Marketing data typically arrives scattered across CSV exports, JSON API
dumps, and Excel workbooks, each with inconsistent column names, missing
values, and duplicate rows.

## Solution

This pipeline provides a single command that:

1. **Loads** every supported file in a directory (`pipeline/loaders.py`) —
   CSV, JSON, Excel, or a live REST API endpoint.
2. **Cleans** each dataset (`pipeline/cleaners.py`) — standardizes column
   names, coerces dtypes, drops duplicates, and imputes/drops missing values.
3. **Merges** the cleaned datasets into one unified table (`pipeline/merger.py`).
4. **Analyzes** the merged data (`pipeline/analyzer.py`) — summary
   statistics, correlation matrix, and outlier detection.
5. **Visualizes** results (`pipeline/visualizer.py`) — distribution
   histograms and a correlation heatmap saved as PNGs.
6. **Reports** everything as a Markdown summary (`pipeline/reporter.py`).

## Project Structure

```
DATA-PIPELINE-AUTOMATION/
├── main.py                  # CLI entry point / orchestrator
├── pipeline/
│   ├── config.py             # paths + logging setup
│   ├── loaders.py            # CSV / JSON / Excel / API ingestion
│   ├── cleaners.py           # cleaning & normalization
│   ├── merger.py             # merge/concat multiple datasets
│   ├── analyzer.py           # summary stats, correlations, outliers
│   ├── visualizer.py         # matplotlib/seaborn plots
│   └── reporter.py           # Markdown report generation
├── data/
│   ├── raw/                  # input files (CSV/JSON/Excel)
│   └── processed/            # cleaned/merged output
├── reports/                  # generated report + figures
├── tests/                    # pytest unit tests
└── requirements.txt
```

## Usage

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Drop your CSV/JSON/Excel files into data/raw/, then:
python main.py
# or point at a custom directory:
python main.py --input path/to/your/data
```

Output:
- `data/processed/merged_dataset.csv` — cleaned, merged dataset
- `reports/summary_report.md` — statistical summary report
- `reports/figures/*.png` — distribution + correlation visualizations

## Running Tests

```bash
pip install pytest
pytest tests/
```

## Notes on "real-time"

Marketing exports (CSV/Excel) and most APIs are batch/pull-based rather
than streaming. This pipeline is designed to be re-run on demand (or on a
schedule, e.g. via cron) against the latest files/API responses — each run
processes whatever is currently in `data/raw/` end-to-end in seconds. For
true event-by-event streaming (e.g. Kafka), a different ingestion layer
would replace `loaders.load_directory`.
