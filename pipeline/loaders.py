"""Data ingestion layer: load raw data from CSV, JSON, Excel, and REST APIs
into a uniform list of (source_name, DataFrame) pairs for downstream cleaning.
"""

from pathlib import Path
from typing import Optional

import pandas as pd
import requests

from pipeline.config import get_logger

logger = get_logger(__name__)


def load_csv(file_path: str, **read_csv_kwargs) -> pd.DataFrame:
    """Load a single CSV file into a DataFrame.

    Args:
        file_path: Path to the .csv file.
        **read_csv_kwargs: Extra keyword args forwarded to pandas.read_csv
            (e.g. sep=";", encoding="latin-1").

    Returns:
        A DataFrame with the CSV contents, or an empty DataFrame if the
        file is missing or cannot be parsed.
    """
    try:
        df = pd.read_csv(file_path, **read_csv_kwargs)
        logger.info("Loaded CSV %s (%d rows, %d cols)", file_path, *df.shape)
        return df
    except FileNotFoundError:
        logger.error("CSV file not found: %s", file_path)
    except pd.errors.EmptyDataError:
        logger.error("CSV file is empty: %s", file_path)
    except pd.errors.ParserError as exc:
        logger.error("Could not parse CSV %s: %s", file_path, exc)
    return pd.DataFrame()


def load_json(file_path: str, record_path: Optional[str] = None) -> pd.DataFrame:
    """Load a JSON file (array of records, or nested with a record_path) into a DataFrame.

    Args:
        file_path: Path to the .json file.
        record_path: Optional dotted key indicating where the list of
            records lives inside a nested JSON object (e.g. "data.items").

    Returns:
        A DataFrame with the JSON contents, or an empty DataFrame on failure.
    """
    import json

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            payload = json.load(f)

        if record_path:
            for key in record_path.split("."):
                payload = payload[key]

        df = pd.json_normalize(payload)
        logger.info("Loaded JSON %s (%d rows, %d cols)", file_path, *df.shape)
        return df
    except FileNotFoundError:
        logger.error("JSON file not found: %s", file_path)
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        logger.error("Could not parse JSON %s: %s", file_path, exc)
    return pd.DataFrame()


def load_excel(file_path: str, sheet_name=0, **read_excel_kwargs) -> pd.DataFrame:
    """Load a sheet from an Excel workbook into a DataFrame.

    Args:
        file_path: Path to the .xlsx/.xls file.
        sheet_name: Sheet name or index to read (default: first sheet).
        **read_excel_kwargs: Extra keyword args forwarded to pandas.read_excel.

    Returns:
        A DataFrame with the sheet contents, or an empty DataFrame on failure.
    """
    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name, **read_excel_kwargs)
        logger.info("Loaded Excel %s (%d rows, %d cols)", file_path, *df.shape)
        return df
    except FileNotFoundError:
        logger.error("Excel file not found: %s", file_path)
    except ValueError as exc:
        logger.error("Could not parse Excel %s: %s", file_path, exc)
    return pd.DataFrame()


def load_api(url: str, params: Optional[dict] = None, timeout: int = 10,
             record_path: Optional[str] = None) -> pd.DataFrame:
    """Fetch JSON data from a REST API endpoint into a DataFrame.

    Args:
        url: Full URL of the API endpoint.
        params: Optional query-string parameters.
        timeout: Request timeout in seconds.
        record_path: Optional dotted key indicating where the list of
            records lives inside a nested JSON response.

    Returns:
        A DataFrame built from the response JSON, or an empty DataFrame
        on any network/parsing error.
    """
    try:
        response = requests.get(url, params=params, timeout=timeout)
        response.raise_for_status()
        payload = response.json()

        if record_path:
            for key in record_path.split("."):
                payload = payload[key]

        df = pd.json_normalize(payload)
        logger.info("Loaded API data from %s (%d rows, %d cols)", url, *df.shape)
        return df
    except requests.exceptions.RequestException as exc:
        logger.error("API request to %s failed: %s", url, exc)
    except (ValueError, KeyError) as exc:
        logger.error("Could not parse API response from %s: %s", url, exc)
    return pd.DataFrame()


def load_directory(directory: str) -> dict:
    """Auto-detect and load every supported file (.csv/.json/.xlsx/.xls) in a directory.

    Args:
        directory: Path to a directory containing raw data files.

    Returns:
        A dict mapping {file_stem: DataFrame} for every successfully loaded file.
    """
    loaders = {
        ".csv": load_csv,
        ".json": load_json,
        ".xlsx": load_excel,
        ".xls": load_excel,
    }
    datasets = {}
    dir_path = Path(directory)

    if not dir_path.exists():
        logger.error("Directory not found: %s", directory)
        return datasets

    for file_path in sorted(dir_path.iterdir()):
        loader = loaders.get(file_path.suffix.lower())
        if loader is None:
            continue
        df = loader(str(file_path))
        if not df.empty:
            datasets[file_path.stem] = df

    logger.info("Loaded %d dataset(s) from %s", len(datasets), directory)
    return datasets
