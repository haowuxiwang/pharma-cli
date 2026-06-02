"""Correlation analysis command."""
import json
import click
from pathlib import Path

from cli.r_engine import run_r_file
from cli.validators import validate_xy
from cli.commands.utils import output


@click.command()
@click.option("--x", multiple=True, type=float, help="First variable values")
@click.option("--y", multiple=True, type=float, help="Second variable values")
@click.option("--file", "-f", "data_file", type=click.Path(exists=True), help="File with data")
@click.option("--x-column", default=None, help="X column name in file")
@click.option("--y-column", default=None, help="Y column name in file")
@click.option("--method", type=click.Choice(["pearson", "spearman", "kendall"]), default="pearson")
def correlation(x, y, data_file, x_column, y_column, method):
    """Correlation analysis: pearson, spearman, kendall.

    Supports Excel (.xlsx, .xls), CSV, JSON, and text files.

    Examples:

    \b
    # From values
    stats-cli correlation --x 1 --x 2 --x 3 --y 2 --y 4 --y 6

    \b
    # From Excel file
    stats-cli correlation -f data.xlsx --x-column "温度" --y-column "收率"

    \b
    # Spearman correlation
    stats-cli correlation -f data.csv --x-column "x" --y-column "y" --method spearman
    """
    if x and y:
        x_list, y_list = validate_xy(x, y)
        data = {"x": x_list, "y": y_list}
    elif data_file:
        data = _load_xy_from_file(data_file, x_column, y_column)
    else:
        raise click.UsageError("provide --x/--y or --file with --x-column/--y-column")

    data["method"] = method
    result = run_r_file("correlation.R", data)
    output(result)


def _load_xy_from_file(file_path, x_column, y_column):
    """Load X and Y data from file (Excel, CSV, JSON, or text)."""
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix in [".xlsx", ".xls"]:
        return _load_xy_from_excel(path, x_column, y_column)
    elif suffix == ".csv":
        return _load_xy_from_csv(path, x_column, y_column)
    elif suffix == ".json":
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return _load_xy_from_text(path)


def _load_xy_from_excel(path, x_column, y_column):
    """Load X and Y from Excel file."""
    import pandas as pd
    import numpy as np

    try:
        df = pd.read_excel(path)
    except Exception as e:
        raise click.UsageError(f"Failed to read Excel: {e}")

    if not x_column or not y_column:
        raise click.UsageError("Excel file requires --x-column and --y-column")

    x_data = _extract_column(df, x_column, "x")
    y_data = _extract_column(df, y_column, "y")

    # Remove rows where either X or Y is NaN
    mask = ~(np.isnan(x_data) | np.isnan(y_data))
    x_data = [x_data[i] for i in range(len(x_data)) if mask[i]]
    y_data = [y_data[i] for i in range(len(y_data)) if mask[i]]

    if len(x_data) < 2:
        raise click.UsageError("Need at least 2 valid data points after removing missing values")

    return {"x": x_data, "y": y_data}


def _load_xy_from_csv(path, x_column, y_column):
    """Load X and Y from CSV file."""
    import csv
    import io
    from cli.data_cleaner import detect_encoding, detect_delimiter

    encoding = detect_encoding(str(path))
    delimiter = detect_delimiter(str(path), encoding)

    content = path.read_text(encoding=encoding).strip()
    reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
    rows = list(reader)

    x_col = x_column or "x"
    y_col = y_column or "y"

    try:
        x_data = [float(r[x_col]) for r in rows if r[x_col]]
        y_data = [float(r[y_col]) for r in rows if r[y_col]]
    except KeyError as e:
        raise click.UsageError(f"Column not found: {e}")

    return {"x": x_data, "y": y_data}


def _load_xy_from_text(path):
    """Load X and Y from text file (tab/space separated pairs)."""
    from cli.data_cleaner import detect_encoding

    encoding = detect_encoding(str(path))
    content = path.read_text(encoding=encoding).strip()
    lines = content.splitlines()
    pairs = [line.split() for line in lines if line.strip()]

    try:
        x_data = [float(p[0]) for p in pairs if len(p) >= 2]
        y_data = [float(p[1]) for p in pairs if len(p) >= 2]
    except (ValueError, IndexError) as e:
        raise click.UsageError(f"Failed to parse text file: {e}")

    return {"x": x_data, "y": y_data}


def _extract_column(df, column, param_name):
    """Extract a column from DataFrame by name or index."""
    # Try as column name
    if column in df.columns:
        return df[column].dropna().astype(float).tolist()

    # Try as column index
    try:
        col_idx = int(column)
        if 0 <= col_idx < len(df.columns):
            return df.iloc[:, col_idx].dropna().astype(float).tolist()
    except (ValueError, IndexError):
        pass

    raise click.UsageError(f"Column '{column}' not found for {param_name}. Available: {list(df.columns)}")
