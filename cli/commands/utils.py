"""Shared utilities for commands."""
import json
import sys
import click
import numpy as np
from pathlib import Path
from datetime import datetime

from cli.r_engine import run_r_file
from cli.validators import validate_values


def load_data(values, data_file, column):
    """Load data from CLI arguments or file."""
    if values:
        return {"values": list(values)}
    elif data_file:
        path = Path(data_file)

        # Support Excel files directly
        if path.suffix in [".xlsx", ".xls"]:
            try:
                import pandas as pd
                df = pd.read_excel(path)

                if column:
                    # Try to find column by name or index
                    col_found = False

                    # Try as column name (string match)
                    if column in df.columns:
                        values = df[column].dropna().tolist()
                        col_found = True

                    # Try as column name (numeric match)
                    if not col_found:
                        try:
                            col_num = float(column)
                            for col in df.columns:
                                if float(col) == col_num:
                                    values = df[col].dropna().tolist()
                                    col_found = True
                                    break
                        except (ValueError, TypeError):
                            pass

                    # Try as column index
                    if not col_found:
                        try:
                            col_idx = int(column)
                            if 0 <= col_idx < len(df.columns):
                                values = df.iloc[:, col_idx].dropna().tolist()
                                col_found = True
                        except (ValueError, IndexError):
                            pass

                    if not col_found:
                        raise click.UsageError(f"Column '{column}' not found in Excel file")
                else:
                    # Use first numeric column
                    numeric_cols = df.select_dtypes(include=[np.number]).columns
                    if len(numeric_cols) > 0:
                        values = df[numeric_cols[0]].dropna().tolist()
                    else:
                        raise click.UsageError("No numeric columns found in Excel file")

                return {"values": [float(v) for v in values]}
            except ImportError:
                raise click.UsageError("pandas is required to read Excel files. Install with: pip install pandas")

        # Read text-based files
        content = path.read_text(encoding="utf-8").strip()

        if path.suffix == ".csv":
            import csv
            import io
            reader = csv.DictReader(io.StringIO(content))
            if column:
                # Try to find column by name or index
                try:
                    values = [float(row[column]) for row in reader]
                except KeyError:
                    # Try as column index
                    try:
                        col_idx = int(column)
                        reader = csv.DictReader(io.StringIO(content))
                        values = [float(list(row.values())[col_idx]) for row in reader]
                    except (ValueError, IndexError):
                        raise click.UsageError(f"Column '{column}' not found in CSV file")
            else:
                # Use first numeric column
                first_row = next(reader)
                col_name = None
                for k, v in first_row.items():
                    try:
                        float(v)
                        col_name = k
                        break
                    except ValueError:
                        continue

                if col_name is None:
                    raise click.UsageError("No numeric columns found in CSV file")

                reader = csv.DictReader(io.StringIO(content))
                values = [float(row[col_name]) for row in reader]
            return {"values": values}
        elif path.suffix == ".json":
            return json.loads(content)
        else:
            # Plain text, one value per line
            values = [float(line) for line in content.splitlines() if line.strip()]
            return {"values": values}
    else:
        # Read from stdin
        content = sys.stdin.read().strip()
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            values = [float(line) for line in content.splitlines() if line.strip()]
            return {"values": values}


def output(data):
    """Output result as JSON."""
    click.echo(json.dumps(data, indent=2, ensure_ascii=False))
