"""Statistical analysis of a cleaned/merged dataset: summary stats,
correlations, and outlier detection.
"""

import numpy as np
import pandas as pd

from pipeline.config import get_logger

logger = get_logger(__name__)


def generate_summary_statistics(df: pd.DataFrame) -> pd.DataFrame:
    """Compute descriptive statistics for all numeric columns.

    Args:
        df: Input DataFrame.

    Returns:
        A DataFrame of describe()-style statistics (count, mean, std, min,
        quartiles, max) transposed so each row is one column of df.
    """
    numeric_df = df.select_dtypes(include="number")
    if numeric_df.empty:
        logger.warning("No numeric columns found for summary statistics")
        return pd.DataFrame()

    summary = numeric_df.describe().T
    logger.info("Generated summary statistics for %d numeric column(s)", len(summary))
    return summary


def compute_correlations(df: pd.DataFrame, method: str = "pearson") -> pd.DataFrame:
    """Compute the pairwise correlation matrix for numeric columns.

    Args:
        df: Input DataFrame.
        method: Correlation method ("pearson", "kendall", or "spearman").

    Returns:
        A correlation matrix DataFrame, or empty if fewer than 2 numeric
        columns are present.
    """
    numeric_df = df.select_dtypes(include="number")
    if numeric_df.shape[1] < 2:
        logger.warning("Fewer than 2 numeric columns; cannot compute correlations")
        return pd.DataFrame()

    corr = numeric_df.corr(method=method)
    logger.info("Computed %s correlation matrix (%dx%d)", method, *corr.shape)
    return corr


def detect_outliers(df: pd.DataFrame, column: str, method: str = "iqr", threshold: float = 1.5) -> pd.DataFrame:
    """Flag outlier rows in a numeric column using the IQR or z-score method.

    Args:
        df: Input DataFrame.
        column: Name of the numeric column to inspect.
        method: "iqr" (Tukey's fences) or "zscore".
        threshold: IQR multiplier (default 1.5) or z-score cutoff (default
            used as 1.5 only for IQR; pass 3.0 explicitly for zscore).

    Returns:
        The subset of df flagged as outliers for the given column. Returns
        an empty DataFrame if the column is missing or non-numeric.

    Raises:
        ValueError: If method is not "iqr" or "zscore".
    """
    if method not in {"iqr", "zscore"}:
        raise ValueError(f"Unsupported outlier method: {method!r}")

    if column not in df.columns or not pd.api.types.is_numeric_dtype(df[column]):
        logger.warning("Column '%s' not found or not numeric; skipping outlier detection", column)
        return pd.DataFrame()

    series = df[column].dropna()

    if method == "iqr":
        q1, q3 = series.quantile(0.25), series.quantile(0.75)
        iqr = q3 - q1
        lower, upper = q1 - threshold * iqr, q3 + threshold * iqr
        mask = (df[column] < lower) | (df[column] > upper)
    else:
        mean, std = series.mean(), series.std(ddof=0)
        if std == 0 or np.isnan(std):
            return pd.DataFrame()
        z_scores = (df[column] - mean) / std
        mask = z_scores.abs() > threshold

    outliers = df[mask]
    logger.info("Detected %d outlier(s) in column '%s' (method=%s)", len(outliers), column, method)
    return outliers


def analyze_dataset(df: pd.DataFrame) -> dict:
    """Run the full analysis suite on a dataset.

    Args:
        df: Cleaned/merged input DataFrame.

    Returns:
        A dict with keys "summary_statistics", "correlations", and
        "row_count"/"column_count" metadata for reporting.
    """
    return {
        "row_count": len(df),
        "column_count": df.shape[1],
        "summary_statistics": generate_summary_statistics(df),
        "correlations": compute_correlations(df),
    }
