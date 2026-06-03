"""Shared utilities for commands."""
import json
import sys
import click
import numpy as np
from pathlib import Path
from datetime import datetime, timezone

from cli.r_engine import run_r_file
from cli.validators import validate_values
from cli.data_cleaner import clean_values, detect_encoding, detect_delimiter, CleaningReport


def load_data(values, data_file, column, sheet=None):
    """Load data from CLI arguments or file.

    All data sources pass through the cleaning layer to handle
    NaN, Inf, non-numeric values, encoding issues, etc.
    """
    if values:
        raw = list(values)
        try:
            cleaned, report = clean_values(raw, min_count=1)
        except ValueError as e:
            raise click.UsageError(str(e))
        result = {"values": cleaned}
        if report.has_changes():
            result["_cleaning_report"] = report.to_dict()
        return result
    elif data_file:
        path = Path(data_file)

        # Support Excel files directly
        if path.suffix in [".xlsx", ".xls"]:
            return _load_excel(path, column, sheet)

        # Read text-based files with encoding detection
        encoding = detect_encoding(str(path))
        content = path.read_text(encoding=encoding).strip()

        if path.suffix == ".csv":
            return _load_csv(path, content, column, encoding)
        elif path.suffix == ".json":
            return _load_json(content)
        else:
            # Plain text, one value per line
            return _load_text(content)
    else:
        # Read from stdin
        content = sys.stdin.read().strip()
        try:
            data = json.loads(content)
            if isinstance(data, dict) and "values" in data:
                try:
                    cleaned, report = clean_values(data["values"], min_count=1)
                except ValueError as e:
                    raise click.UsageError(str(e))
                data["values"] = cleaned
                if report.has_changes():
                    data["_cleaning_report"] = report.to_dict()
                return data
            return data
        except json.JSONDecodeError:
            return _load_text(content)


def _load_excel(path, column, sheet=None):
    """Load data from Excel file with proper error handling."""
    try:
        import pandas as pd
    except ImportError:
        raise click.UsageError("pandas is required to read Excel files. Install with: pip install pandas")

    try:
        # When sheet is None, pd.read_excel returns first sheet as DataFrame
        # When sheet is a string, it returns that specific sheet as DataFrame
        # When sheet is 0, it returns first sheet as DataFrame
        if sheet is None:
            df = pd.read_excel(path, sheet_name=0)  # Read first sheet
        else:
            df = pd.read_excel(path, sheet_name=sheet)
    except Exception as e:
        raise click.UsageError(f"Failed to read Excel file: {e}")

    if column:
        values = _extract_excel_column(df, column, path)
    else:
        # Use first numeric column
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) == 0:
            raise click.UsageError("No numeric columns found in Excel file")
        values = df[numeric_cols[0]].dropna().tolist()

    # Convert to float, handling datetime columns
    raw_values = []
    for v in values:
        if isinstance(v, (int, float)):
            raw_values.append(v)
        elif hasattr(v, 'timestamp'):
            # datetime-like: convert to timestamp
            raw_values.append(v.timestamp())
        else:
            raw_values.append(v)

    try:
        cleaned, report = clean_values(raw_values, min_count=1)
    except ValueError as e:
        raise click.UsageError(str(e))
    result = {"values": cleaned}
    if report.has_changes():
        result["_cleaning_report"] = report.to_dict()
    return result


def _extract_excel_column(df, column, path):
    """Extract a column from Excel DataFrame by name, numeric name, or index."""
    # Try as column name (string match)
    if column in df.columns:
        return df[column].dropna().tolist()

    # Try as column name (numeric match)
    try:
        col_num = float(column)
        for col in df.columns:
            if float(col) == col_num:
                return df[col].dropna().tolist()
    except (ValueError, TypeError):
        pass

    # Try as column index
    try:
        col_idx = int(column)
        if 0 <= col_idx < len(df.columns):
            return df.iloc[:, col_idx].dropna().tolist()
    except (ValueError, IndexError):
        pass

    raise click.UsageError(f"Column '{column}' not found in Excel file")


def _load_csv(path, content, column, encoding="utf-8"):
    """Load data from CSV file with delimiter detection and BOM handling."""
    import csv
    import io

    # Detect delimiter
    delimiter = detect_delimiter(str(path), encoding)

    # Strip BOM from content
    if content.startswith('﻿'):
        content = content[1:]

    reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)

    if column:
        values = _extract_csv_column(reader, column, content, delimiter)
    else:
        # Use first numeric column
        first_row = next(reader)
        col_name = None
        for k, v in first_row.items():
            try:
                float(v)
                col_name = k
                break
            except (ValueError, TypeError):
                continue

        if col_name is None:
            raise click.UsageError("No numeric columns found in CSV file")

        reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
        values = []
        for row in reader:
            try:
                values.append(float(row[col_name]))
            except (ValueError, TypeError):
                pass  # Skip non-numeric rows

    try:
        cleaned, report = clean_values(values, min_count=1)
    except ValueError as e:
        raise click.UsageError(str(e))
    result = {"values": cleaned}
    if report.has_changes():
        result["_cleaning_report"] = report.to_dict()
    return result


def _extract_csv_column(reader, column, content, delimiter):
    """Extract a column from CSV by name or index."""
    import csv
    import io

    # Try as column name
    try:
        values = []
        for row in reader:
            try:
                values.append(float(row[column]))
            except (ValueError, TypeError):
                pass  # Skip non-numeric rows
        if values:
            return values
    except KeyError:
        pass

    # Try as column index
    try:
        col_idx = int(column)
        reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
        values = []
        for row in reader:
            try:
                values.append(float(list(row.values())[col_idx]))
            except (ValueError, TypeError, IndexError):
                pass
        if values:
            return values
    except (ValueError, IndexError):
        pass

    raise click.UsageError(f"Column '{column}' not found in CSV file")


def _load_json(content):
    """Load data from JSON content."""
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        raise click.UsageError(f"Invalid JSON: {e}")

    if isinstance(data, dict) and "values" in data:
        try:
            cleaned, report = clean_values(data["values"], min_count=1)
        except ValueError as e:
            raise click.UsageError(str(e))
        data["values"] = cleaned
        if report.has_changes():
            data["_cleaning_report"] = report.to_dict()
    return data


def _load_text(content):
    """Load data from plain text (one value per line)."""
    raw_values = []
    for line in content.splitlines():
        line = line.strip()
        if line:
            try:
                raw_values.append(float(line))
            except ValueError:
                pass  # Skip non-numeric lines

    try:
        cleaned, report = clean_values(raw_values, min_count=1)
    except ValueError as e:
        raise click.UsageError(str(e))
    result = {"values": cleaned}
    if report.has_changes():
        result["_cleaning_report"] = report.to_dict()
    return result


def output(data):
    """Output result as JSON with metadata wrapper.

    Wraps the result with standard metadata:
    - status: "success" or "error"
    - version: CLI version
    - timestamp: ISO format timestamp

    If data contains an error, formats as error response.
    """
    # Check if data is an error response
    if isinstance(data, dict) and data.get("error"):
        wrapped = {
            "status": "error",
            "version": "0.4.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": True,
            "error_type": data.get("error_type", "UNKNOWN_ERROR"),
            "message": data.get("message", "Unknown error"),
        }
        if "suggestion" in data:
            wrapped["suggestion"] = data["suggestion"]
    else:
        wrapped = {
            "status": "success",
            "version": "0.4.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data,
        }

    click.echo(json.dumps(wrapped, indent=2, ensure_ascii=False))
