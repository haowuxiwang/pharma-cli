"""Outlier detection command."""
import click

from cli.r_engine import run_r_file
from cli.validators import validate_values, validate_alpha
from cli.commands.utils import load_data, output


@click.command()
@click.option("--values", "-v", multiple=True, type=float, help="Data values")
@click.option("--file", "-f", "data_file", type=click.Path(exists=True), help="File with data")
@click.option("--column", "-c", default=None, help="Column name if file is CSV/TSV")
@click.option("--sheet", "-s", default=None, help="Excel sheet name (default: first sheet)")
@click.option("--method", type=click.Choice(["grubbs", "dixon", "iqr", "zscore"]), default="grubbs")
@click.option("--alpha", type=float, default=0.05, help="Significance level")
def outlier(values, data_file, column, sheet, method, alpha):
    """Outlier detection: grubbs, dixon, iqr, zscore."""
    alpha = validate_alpha(alpha)
    data = load_data(values, data_file, column, sheet)
    if "values" in data:
        validate_values(tuple(data["values"]), min_count=3, name="values")
    data["method"] = method
    data["alpha"] = alpha
    result = run_r_file("outlier.R", data)
    output(result)
