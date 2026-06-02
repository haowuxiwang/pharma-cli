"""Data transformation command."""
import json
import click

from cli.r_engine import run_r_file
from cli.commands.utils import load_data, output


@click.command()
@click.option("--values", "-v", multiple=True, type=float, help="Data values")
@click.option("--file", "-f", "data_file", type=click.Path(exists=True), help="File with data")
@click.option("--column", "-c", default=None, help="Column name if file is CSV/TSV")
@click.option("--sheet", "-s", default=None, help="Excel sheet name (default: first sheet)")
@click.option("--method", type=click.Choice(["log", "sqrt", "boxcox", "johnson", "rank", "standardize", "recip"]),
              required=True, help="Transformation method")
def transform(values, data_file, column, sheet, method):
    """Transform data: normalize, stabilize variance, or change scale.

    Methods:

    \b
    - log: Logarithmic transformation (handles non-positive values)
    - sqrt: Square root transformation
    - boxcox: Box-Cox transformation (finds optimal lambda)
    - johnson: Johnson transformation (log approximation)
    - rank: Rank transformation
    - standardize: Z-score standardization
    - recip: Reciprocal transformation (1/x)

    Examples:

    \b
    # Log transformation
    stats-cli transform -f data.csv -c "weight" --method log

    \b
    # Box-Cox transformation
    stats-cli transform -v 10.2 -v 10.5 -v 10.1 --method boxcox

    \b
    # Standardize data
    stats-cli transform -f data.xlsx -c "yield" --method standardize
    """
    data = load_data(values, data_file, column, sheet)
    data["method"] = method

    result = run_r_file("transform.R", data)
    output(result)
