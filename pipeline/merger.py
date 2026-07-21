"""Merge multiple cleaned datasets into a single unified DataFrame."""

import pandas as pd

from pipeline.config import get_logger

logger = get_logger(__name__)


def merge_on_keys(datasets: dict, keys: list, how: str = "outer") -> pd.DataFrame:
    """Merge multiple DataFrames together on one or more shared key columns.

    Args:
        datasets: Dict mapping {name: DataFrame} of cleaned datasets.
        keys: Column name(s) present in all datasets to join on.
        how: Join type forwarded to pandas.merge (default "outer" to avoid
            silently dropping rows that don't match across every source).

    Returns:
        A single merged DataFrame. If only one dataset is provided, it is
        returned unchanged. Datasets missing any key column are skipped
        with a logged warning.
    """
    usable = {}
    for name, df in datasets.items():
        if all(key in df.columns for key in keys):
            usable[name] = df
        else:
            logger.warning("Skipping dataset '%s': missing key column(s) %s", name, keys)

    if not usable:
        logger.error("No datasets contain the required key(s) %s", keys)
        return pd.DataFrame()

    names = list(usable.keys())
    merged = usable[names[0]]
    for name in names[1:]:
        merged = pd.merge(
            merged, usable[name], on=keys, how=how, suffixes=("", f"_{name}")
        )

    logger.info("Merged %d dataset(s) on %s -> %d rows, %d cols",
                len(usable), keys, *merged.shape)
    return merged


def concat_datasets(datasets: dict, ignore_index: bool = True) -> pd.DataFrame:
    """Stack multiple DataFrames with the same schema on top of each other.

    Args:
        datasets: Dict mapping {name: DataFrame}.
        ignore_index: Whether to reset the row index after concatenation.

    Returns:
        A single concatenated DataFrame. A "source" column is added to
        track which dataset each row originated from.
    """
    if not datasets:
        logger.error("No datasets provided to concatenate")
        return pd.DataFrame()

    tagged = []
    for name, df in datasets.items():
        df = df.copy()
        df["source"] = name
        tagged.append(df)

    combined = pd.concat(tagged, ignore_index=ignore_index)
    logger.info("Concatenated %d dataset(s) -> %d rows, %d cols",
                len(datasets), *combined.shape)
    return combined
