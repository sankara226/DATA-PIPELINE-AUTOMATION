"""Unit tests covering cleaners, merger, and analyzer with small in-memory DataFrames."""

import pandas as pd

from pipeline.analyzer import compute_correlations, detect_outliers, generate_summary_statistics
from pipeline.cleaners import clean_dataset, handle_missing_values, remove_duplicates, standardize_columns
from pipeline.merger import concat_datasets, merge_on_keys


def test_standardize_columns():
    df = pd.DataFrame({"  First Name ": [1], "Last-Name!!": [2]})
    result = standardize_columns(df)
    assert list(result.columns) == ["first_name", "last_name"]


def test_handle_missing_values_drop():
    df = pd.DataFrame({"a": [1, None, 3]})
    result = handle_missing_values(df, strategy="drop")
    assert len(result) == 2


def test_handle_missing_values_fill_numeric_uses_median():
    df = pd.DataFrame({"a": [1.0, None, 3.0]})
    result = handle_missing_values(df, strategy="fill")
    assert result["a"].isna().sum() == 0
    assert result["a"].iloc[1] == 2.0


def test_remove_duplicates():
    df = pd.DataFrame({"a": [1, 1, 2]})
    result = remove_duplicates(df)
    assert len(result) == 2


def test_clean_dataset_end_to_end():
    df = pd.DataFrame({"Amount ": ["10", "10", None], "Date": ["2026-01-01", "2026-01-01", "2026-01-02"]})
    result = clean_dataset(df, numeric_columns=["amount"], date_columns=["date"])
    assert "amount" in result.columns
    assert pd.api.types.is_datetime64_any_dtype(result["date"])


def test_concat_datasets_adds_source_column():
    datasets = {"a": pd.DataFrame({"x": [1]}), "b": pd.DataFrame({"x": [2]})}
    result = concat_datasets(datasets)
    assert set(result["source"]) == {"a", "b"}
    assert len(result) == 2


def test_merge_on_keys_skips_missing_key_column():
    datasets = {
        "a": pd.DataFrame({"id": [1, 2], "val": [10, 20]}),
        "b": pd.DataFrame({"other": [1, 2], "val2": [30, 40]}),
    }
    result = merge_on_keys(datasets, keys=["id"])
    assert list(result.columns) == ["id", "val"]


def test_generate_summary_statistics():
    df = pd.DataFrame({"x": [1, 2, 3], "y": ["a", "b", "c"]})
    summary = generate_summary_statistics(df)
    assert "x" in summary.index
    assert "y" not in summary.index


def test_compute_correlations_requires_two_numeric_columns():
    df = pd.DataFrame({"x": [1, 2, 3]})
    assert compute_correlations(df).empty


def test_detect_outliers_iqr():
    df = pd.DataFrame({"x": [1, 2, 3, 4, 100]})
    outliers = detect_outliers(df, "x", method="iqr")
    assert 100 in outliers["x"].values
