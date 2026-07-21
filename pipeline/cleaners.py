"""Data cleaning utilities: standardize columns, handle missing values,
fix dtypes, and drop duplicates so downstream merging/analysis is reliable.
"""

import pandas as pd

from pipeline.config import get_logger

logger = get_logger(__name__)


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Lowercase, strip, and snake_case all column names.

    Args:
        df: Input DataFrame.

    Returns:
        A copy of df with normalized column names.
    """
    df = df.copy()
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(r"[^\w]+", "_", regex=True)
        .str.strip("_")
    )
    return df


def handle_missing_values(df: pd.DataFrame, strategy: str = "drop",
                           fill_value=None) -> pd.DataFrame:
    """Handle missing values in a DataFrame.

    Args:
        df: Input DataFrame.
        strategy: One of "drop" (remove rows with any NA), "fill" (use
            fill_value or column-wise median/mode), or "none" (no-op).
        fill_value: Value to use when strategy="fill" and an explicit
            value is desired instead of median/mode imputation.

    Returns:
        A cleaned copy of df.

    Raises:
        ValueError: If an unsupported strategy is passed.
    """
    if strategy not in {"drop", "fill", "none"}:
        raise ValueError(f"Unsupported missing-value strategy: {strategy!r}")

    df = df.copy()
    missing_before = int(df.isna().sum().sum())

    if strategy == "none" or missing_before == 0:
        return df

    if strategy == "drop":
        df = df.dropna()
    elif strategy == "fill":
        if fill_value is not None:
            df = df.fillna(fill_value)
        else:
            for col in df.columns:
                if df[col].isna().any():
                    if pd.api.types.is_numeric_dtype(df[col]):
                        df[col] = df[col].fillna(df[col].median())
                    else:
                        mode = df[col].mode(dropna=True)
                        df[col] = df[col].fillna(mode.iloc[0] if not mode.empty else "unknown")

    logger.info(
        "Handled missing values (strategy=%s): %d -> %d missing cells",
        strategy, missing_before, int(df.isna().sum().sum()),
    )
    return df


def remove_duplicates(df: pd.DataFrame, subset=None) -> pd.DataFrame:
    """Drop duplicate rows from a DataFrame.

    Args:
        df: Input DataFrame.
        subset: Optional list of columns to consider when identifying duplicates.

    Returns:
        A deduplicated copy of df.
    """
    before = len(df)
    df = df.drop_duplicates(subset=subset).reset_index(drop=True)
    removed = before - len(df)
    if removed:
        logger.info("Removed %d duplicate row(s)", removed)
    return df


def coerce_dtypes(df: pd.DataFrame, date_columns=None, numeric_columns=None) -> pd.DataFrame:
    """Coerce specific columns to datetime/numeric dtypes, ignoring failures per value.

    Args:
        df: Input DataFrame.
        date_columns: Column names to parse as datetimes.
        numeric_columns: Column names to parse as numeric values.

    Returns:
        A copy of df with the requested columns coerced. Values that fail
        to parse become NaT/NaN rather than raising.
    """
    df = df.copy()
    for col in date_columns or []:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    for col in numeric_columns or []:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def clean_dataset(df: pd.DataFrame, missing_strategy: str = "fill",
                   date_columns=None, numeric_columns=None) -> pd.DataFrame:
    """Run the full cleaning pipeline on a single DataFrame.

    Applies, in order: column standardization, dtype coercion, duplicate
    removal, and missing-value handling.

    Args:
        df: Raw input DataFrame.
        missing_strategy: Strategy forwarded to handle_missing_values.
        date_columns: Columns to coerce to datetime.
        numeric_columns: Columns to coerce to numeric.

    Returns:
        A fully cleaned DataFrame ready for merging/analysis.
    """
    df = standardize_columns(df)
    df = coerce_dtypes(df, date_columns=date_columns, numeric_columns=numeric_columns)
    df = remove_duplicates(df)
    df = handle_missing_values(df, strategy=missing_strategy)
    return df
