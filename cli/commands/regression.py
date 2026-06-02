"""Regression analysis command."""
import json
import click
from pathlib import Path
from datetime import datetime

from cli.r_engine import run_r_file
from cli.validators import validate_xy
from cli.commands.utils import output


@click.command()
@click.option("--x", multiple=True, type=float, help="Independent variable values")
@click.option("--y", multiple=True, type=float, help="Dependent variable values")
@click.option("--file", "-f", "data_file", type=click.Path(exists=True), help="File with data")
@click.option("--x-column", default=None, help="X column name in file")
@click.option("--y-column", default=None, help="Y column name in file")
@click.option("--x-columns", multiple=True, help="X column names for multiple/stepwise regression")
@click.option("--type", "reg_type", type=click.Choice([
    "linear", "quadratic", "polynomial", "multiple", "logistic", "stepwise"
]), default="linear")
@click.option("--degree", type=int, default=3, help="Polynomial degree (for polynomial type)")
@click.option("--direction", type=click.Choice(["both", "forward", "backward"]), default="both",
              help="Stepwise direction")
@click.pass_context
def regression(ctx, x, y, data_file, x_column, y_column, x_columns, reg_type, degree, direction):
    """Regression analysis: linear, quadratic, polynomial, multiple, logistic, stepwise.

    Supports Excel (.xlsx, .xls), CSV, and text files.

    Examples:

    \b
    # Linear regression
    stats-cli regression --x 1 --x 2 --x 3 --y 2 --y 4 --y 6

    \b
    # Multiple regression
    stats-cli regression -f data.csv --y-column "y" --x-columns "x1" --x-columns "x2" --type multiple

    \b
    # Logistic regression
    stats-cli regression --x 1 --x 2 --x 3 --x 4 --x 5 --y 0 --y 0 --y 1 --y 1 --y 1 --type logistic

    \b
    # Stepwise regression
    stats-cli regression -f data.xlsx --y-column "yield" --x-columns "temp" --x-columns "time" --type stepwise
    """
    if reg_type in ["multiple", "stepwise"]:
        # Multiple/stepwise regression needs data file
        if not data_file:
            raise click.UsageError(f"--type {reg_type} requires --file with data")
        data = _load_regression_data(data_file, y_column, list(x_columns) if x_columns else None)
        data["reg_type"] = reg_type
        data["direction"] = direction
    elif reg_type == "logistic":
        if x and y:
            x_list, y_list = validate_xy(x, y)
            data = {"x": x_list, "y": y_list}
        elif data_file:
            data = _load_xy_from_file(data_file, x_column, y_column)
        else:
            raise click.UsageError("provide --x/--y or --file")
        data["reg_type"] = "logistic"
    else:
        # Linear/quadratic/polynomial
        if x and y:
            x_list, y_list = validate_xy(x, y)
            data = {"x": x_list, "y": y_list}
        elif data_file:
            data = _load_xy_from_file(data_file, x_column, y_column)
        else:
            raise click.UsageError("provide --x/--y or --file with --x-column/--y-column")
        data["reg_type"] = reg_type
        data["degree"] = degree

    result = run_r_file("regression.R", data)

    # Generate interactive diagnostic plots if requested
    if ctx.obj.get("interactive") and reg_type in ["linear", "quadratic", "polynomial"]:
        from cli.charts import create_diagnostic_plots
        plots = create_diagnostic_plots(result)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        interactive_charts = {}
        for plot_name, html in plots.items():
            filename = f"regression_{plot_name}_{timestamp}.html"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html)
            interactive_charts[plot_name] = filename
        result['interactive_charts'] = interactive_charts

    output(result)


def _load_regression_data(file_path, y_column, x_columns):
    """Load data for multiple/stepwise regression from file."""
    from pathlib import Path
    import pandas as pd

    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix in [".xlsx", ".xls"]:
        df = pd.read_excel(path)
    elif suffix == ".csv":
        from cli.data_cleaner import detect_encoding, detect_delimiter
        encoding = detect_encoding(str(path))
        delimiter = detect_delimiter(str(path), encoding)
        df = pd.read_csv(path, encoding=encoding, sep=delimiter)
    else:
        raise click.UsageError(f"Unsupported file format: {suffix}")

    if not y_column:
        raise click.UsageError("--y-column required for multiple/stepwise regression")

    # Auto-detect x columns if not specified
    if not x_columns:
        x_columns = [c for c in df.select_dtypes(include=[float, int]).columns if c != y_column]

    # Convert to dict for R
    data_df = df[[y_column] + list(x_columns)].dropna()
    data = {
        "data": data_df.to_dict(orient="list"),
        "y_column": y_column,
        "x_columns": list(x_columns)
    }
    return data


def _load_xy_from_file(file_path, x_column, y_column):
    """Load X and Y data from file."""
    from pathlib import Path
    import pandas as pd

    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix in [".xlsx", ".xls"]:
        df = pd.read_excel(path)
    elif suffix == ".csv":
        from cli.data_cleaner import detect_encoding, detect_delimiter
        encoding = detect_encoding(str(path))
        delimiter = detect_delimiter(str(path), encoding)
        df = pd.read_csv(path, encoding=encoding, sep=delimiter)
    else:
        raise click.UsageError(f"Unsupported file format: {suffix}")

    # Auto-detect columns if not specified
    if not x_column or not y_column:
        numeric_cols = df.select_dtypes(include=[float, int]).columns.tolist()
        if len(numeric_cols) >= 2:
            x_column = x_column or numeric_cols[0]
            y_column = y_column or numeric_cols[1]
        else:
            raise click.UsageError("--x-column and --y-column required")

    x_data = _extract_column(df, x_column, "x")
    y_data = _extract_column(df, y_column, "y")

    import numpy as np
    mask = ~(np.isnan(x_data) | np.isnan(y_data))
    x_data = [x_data[i] for i in range(len(x_data)) if mask[i]]
    y_data = [y_data[i] for i in range(len(y_data)) if mask[i]]

    return {"x": x_data, "y": y_data}


def _extract_column(df, column, param_name):
    """Extract a column from DataFrame."""
    if column in df.columns:
        return df[column].dropna().astype(float).tolist()
    try:
        col_idx = int(column)
        if 0 <= col_idx < len(df.columns):
            return df.iloc[:, col_idx].dropna().astype(float).tolist()
    except (ValueError, IndexError):
        pass
    raise click.UsageError(f"Column '{column}' not found. Available: {list(df.columns)}")
