"""Explore command - inspect data file structure."""
import json
import click
import sys
import pandas as pd
import numpy as np
from pathlib import Path

from cli.commands.utils import output


@click.command()
@click.option("--file", "-f", "data_file", type=click.Path(exists=True), required=True, help="Data file to explore")
@click.option("--sheet", "-s", default=None, help="Sheet name for Excel files")
@click.option("--rows", "-n", type=int, default=5, help="Number of sample rows to show")
def explore(data_file, sheet, rows):
    """Explore data file structure: columns, types, missing values, basic stats.

    Use this command first when you receive a data file and need to understand
    its structure before running analysis.

    Examples:

    \b
    # Explore Excel file
    stats-cli explore -f data.xlsx

    \b
    # Explore specific sheet
    stats-cli explore -f data.xlsx -s "Sheet1"

    \b
    # Show 10 sample rows
    stats-cli explore -f data.csv -n 10
    """
    path = Path(data_file)
    suffix = path.suffix.lower()

    if suffix in [".xlsx", ".xls"]:
        result = _explore_excel(path, sheet, rows)
    elif suffix == ".csv":
        result = _explore_csv(path, rows)
    elif suffix == ".json":
        result = _explore_json(path, rows)
    else:
        result = _explore_text(path, rows)

    output(result)


def _explore_excel(path, sheet, n_rows):
    """Explore Excel file structure."""
    try:
        # Get sheet names
        xl = pd.ExcelFile(path)
        sheet_names = xl.sheet_names

        # Read the target sheet
        if sheet:
            if sheet not in sheet_names:
                return {"error": True, "message": f"Sheet '{sheet}' not found. Available: {sheet_names}"}
            df = pd.read_excel(path, sheet_name=sheet)
        else:
            df = pd.read_excel(path)
            sheet = sheet_names[0]

        return _build_result(df, str(path), sheet, n_rows, sheet_names)

    except Exception as e:
        return {"error": True, "message": f"Failed to read Excel: {e}"}


def _explore_csv(path, n_rows):
    """Explore CSV file structure."""
    from cli.data_cleaner import detect_encoding, detect_delimiter

    try:
        encoding = detect_encoding(str(path))
        delimiter = detect_delimiter(str(path), encoding)

        df = pd.read_csv(path, encoding=encoding, sep=delimiter)

        delimiter_name = {",": "comma", ";": "semicolon", "\t": "tab", "|": "pipe"}.get(delimiter, delimiter)

        result = _build_result(df, str(path), None, n_rows)
        result["encoding"] = encoding
        result["delimiter"] = delimiter_name
        return result

    except Exception as e:
        return {"error": True, "message": f"Failed to read CSV: {e}"}


def _explore_json(path, n_rows):
    """Explore JSON file structure."""
    try:
        df = pd.read_json(path)
        return _build_result(df, str(path), None, n_rows)
    except Exception:
        # Try as nested JSON
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {
            "file": str(path),
            "format": "json",
            "type": type(data).__name__,
            "keys": list(data.keys()) if isinstance(data, dict) else None,
            "length": len(data) if isinstance(data, (list, dict)) else None,
        }


def _explore_text(path, n_rows):
    """Explore text file structure."""
    from cli.data_cleaner import detect_encoding

    try:
        encoding = detect_encoding(str(path))
        with open(path, "r", encoding=encoding) as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]

        # Try to parse as numbers
        numeric_count = 0
        for line in lines[:100]:
            try:
                float(line)
                numeric_count += 1
            except ValueError:
                pass

        return {
            "file": str(path),
            "format": "text",
            "encoding": encoding,
            "total_lines": len(lines),
            "numeric_lines": numeric_count,
            "sample_values": lines[:n_rows],
            "is_numeric": numeric_count > len(lines[:100]) * 0.8,
        }
    except Exception as e:
        return {"error": True, "message": f"Failed to read text: {e}"}


def _build_result(df, file_path, sheet, n_rows, sheet_names=None):
    """Build exploration result from DataFrame."""
    columns_info = []
    numeric_columns = []

    for col in df.columns:
        dtype = str(df[col].dtype)
        n_missing = int(df[col].isna().sum())
        n_unique = int(df[col].nunique())

        info = {
            "name": str(col),
            "dtype": dtype,
            "n_missing": n_missing,
            "n_unique": n_unique,
        }

        # Add stats for numeric columns
        if np.issubdtype(df[col].dtype, np.number):
            numeric_columns.append(str(col))
            clean = df[col].dropna()
            if len(clean) > 0:
                info["min"] = round(float(clean.min()), 4)
                info["max"] = round(float(clean.max()), 4)
                info["mean"] = round(float(clean.mean()), 4)
                info["std"] = round(float(clean.std()), 4) if len(clean) > 1 else 0

        columns_info.append(info)

    # Sample data
    sample_df = df.head(n_rows)
    sample_data = []
    for _, row in sample_df.iterrows():
        row_dict = {}
        for col in df.columns:
            val = row[col]
            if pd.isna(val):
                row_dict[str(col)] = None
            elif isinstance(val, (np.integer, np.int64)):
                row_dict[str(col)] = int(val)
            elif isinstance(val, (np.floating, np.float64)):
                row_dict[str(col)] = round(float(val), 4)
            else:
                row_dict[str(col)] = str(val)
        sample_data.append(row_dict)

    result = {
        "file": file_path,
        "format": "excel" if sheet_names else "csv",
        "n_rows": len(df),
        "n_columns": len(df.columns),
        "columns": columns_info,
        "numeric_columns": numeric_columns,
        "sample_data": sample_data,
    }

    if sheet_names:
        result["sheet"] = sheet
        result["sheets"] = sheet_names

    return result
