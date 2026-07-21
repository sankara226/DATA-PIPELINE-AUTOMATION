"""Generate visualizations (distributions, correlation heatmap, trends)
from a cleaned dataset and save them as PNG files.
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # non-interactive backend, safe for headless/CI runs
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from pipeline.config import get_logger

logger = get_logger(__name__)


def plot_distributions(df: pd.DataFrame, output_dir: str, max_columns: int = 6) -> list:
    """Plot histograms for numeric columns.

    Args:
        df: Input DataFrame.
        output_dir: Directory to save the generated PNG files into.
        max_columns: Maximum number of numeric columns to plot (to avoid
            generating an unbounded number of figures).

    Returns:
        List of file paths written.
    """
    numeric_cols = df.select_dtypes(include="number").columns[:max_columns]
    if len(numeric_cols) == 0:
        logger.warning("No numeric columns available to plot distributions")
        return []

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    written = []

    for col in numeric_cols:
        fig, ax = plt.subplots(figsize=(6, 4))
        sns.histplot(df[col].dropna(), kde=True, ax=ax)
        ax.set_title(f"Distribution of {col}")
        fig.tight_layout()

        path = Path(output_dir) / f"distribution_{col}.png"
        fig.savefig(path)
        plt.close(fig)
        written.append(str(path))

    logger.info("Saved %d distribution plot(s) to %s", len(written), output_dir)
    return written


def plot_correlation_heatmap(corr: pd.DataFrame, output_dir: str) -> str:
    """Plot a heatmap of a correlation matrix.

    Args:
        corr: Correlation matrix, typically from analyzer.compute_correlations.
        output_dir: Directory to save the generated PNG file into.

    Returns:
        Path to the saved PNG file, or an empty string if corr is empty.
    """
    if corr.empty:
        logger.warning("Empty correlation matrix; skipping heatmap")
        return ""

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(max(6, len(corr) * 0.8), max(5, len(corr) * 0.8)))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", center=0, ax=ax)
    ax.set_title("Correlation Heatmap")
    fig.tight_layout()

    path = Path(output_dir) / "correlation_heatmap.png"
    fig.savefig(path)
    plt.close(fig)

    logger.info("Saved correlation heatmap to %s", path)
    return str(path)


def plot_trend(df: pd.DataFrame, date_column: str, value_column: str, output_dir: str) -> str:
    """Plot a value column over time, aggregated by date.

    Args:
        df: Input DataFrame containing a datetime column and a numeric column.
        date_column: Name of the datetime column.
        value_column: Name of the numeric column to aggregate and plot.
        output_dir: Directory to save the generated PNG file into.

    Returns:
        Path to the saved PNG file, or an empty string if columns are missing/invalid.
    """
    if date_column not in df.columns or value_column not in df.columns:
        logger.warning("Missing column(s) '%s'/'%s'; skipping trend plot", date_column, value_column)
        return ""

    trend_df = df[[date_column, value_column]].dropna()
    if trend_df.empty:
        logger.warning("No data available to plot trend for '%s'", value_column)
        return ""

    trend_df = trend_df.groupby(date_column)[value_column].sum().sort_index()

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 4))
    trend_df.plot(ax=ax)
    ax.set_title(f"{value_column} over time")
    ax.set_xlabel(date_column)
    ax.set_ylabel(value_column)
    fig.tight_layout()

    path = Path(output_dir) / f"trend_{value_column}.png"
    fig.savefig(path)
    plt.close(fig)

    logger.info("Saved trend plot to %s", path)
    return str(path)
