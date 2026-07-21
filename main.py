"""Entry point: run the full marketing-data pipeline end to end.

Usage:
    python main.py                     # process every file in data/raw
    python main.py --input data/raw    # explicit input directory
"""

import argparse
from pathlib import Path

from pipeline.analyzer import analyze_dataset
from pipeline.cleaners import clean_dataset
from pipeline.config import PROCESSED_DATA_DIR, RAW_DATA_DIR, REPORTS_DIR, get_logger
from pipeline.loaders import load_directory
from pipeline.merger import concat_datasets
from pipeline.reporter import generate_report
from pipeline.visualizer import plot_correlation_heatmap, plot_distributions

logger = get_logger(__name__)


def run_pipeline(input_dir: str = str(RAW_DATA_DIR)) -> dict:
    """Run the end-to-end pipeline: load -> clean -> merge -> analyze -> report.

    Args:
        input_dir: Directory containing raw CSV/JSON/Excel files.

    Returns:
        A dict with paths to the processed dataset, report, and plots, or
        an empty dict if no data could be loaded.
    """
    logger.info("Starting pipeline run for input_dir=%s", input_dir)

    raw_datasets = load_directory(input_dir)
    if not raw_datasets:
        logger.error("No datasets loaded from %s; aborting pipeline run", input_dir)
        return {}

    cleaned_datasets = {name: clean_dataset(df) for name, df in raw_datasets.items()}
    merged = concat_datasets(cleaned_datasets)

    processed_path = Path(PROCESSED_DATA_DIR) / "merged_dataset.csv"
    merged.to_csv(processed_path, index=False)
    logger.info("Saved processed dataset to %s", processed_path)

    analysis = analyze_dataset(merged)

    image_paths = plot_distributions(merged, str(REPORTS_DIR / "figures"))
    heatmap_path = plot_correlation_heatmap(analysis["correlations"], str(REPORTS_DIR / "figures"))
    if heatmap_path:
        image_paths.append(heatmap_path)

    report_path = generate_report(
        analysis, image_paths, str(REPORTS_DIR / "summary_report.md"),
        title="Marketing Data Pipeline Report",
    )

    logger.info("Pipeline run complete")
    return {
        "processed_dataset": str(processed_path),
        "report": report_path,
        "figures": image_paths,
    }


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Run the marketing data automation pipeline.")
    parser.add_argument(
        "--input", default=str(RAW_DATA_DIR),
        help="Directory containing raw data files (CSV/JSON/Excel). Default: data/raw",
    )
    args = parser.parse_args()

    results = run_pipeline(args.input)
    if results:
        print("Pipeline finished successfully:")
        for key, value in results.items():
            print(f"  {key}: {value}")
    else:
        print("Pipeline did not produce output. Check pipeline.log for details.")


if __name__ == "__main__":
    main()
