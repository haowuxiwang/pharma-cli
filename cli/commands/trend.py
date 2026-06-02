"""Trend analysis command."""
import click

from cli.r_engine import run_r_file
from cli.commands.utils import load_data, output


@click.command()
@click.option("--values", "-v", multiple=True, type=float, help="Data values")
@click.option("--file", "-f", "data_file", type=click.Path(exists=True), help="File with data")
@click.option("--column", "-c", default=None, help="Column name if file is CSV/TSV")
@click.option("--sheet", "-s", default=None, help="Excel sheet name (default: first sheet)")
@click.option("--test-type", type=click.Choice(["cusum", "ewma", "runs"]), default="cusum")
@click.option("--target", type=float, default=None, help="Target value (for cusum/ewma)")
@click.option("--ewma-lambda", type=float, default=0.2, help="EWMA lambda parameter")
def trend(values, data_file, column, sheet, test_type, target, ewma_lambda):
    """Trend analysis: cusum, ewma, runs test."""
    data = load_data(values, data_file, column, sheet)
    data["test_type"] = test_type
    if target is not None:
        data["target"] = target
    data["lambda"] = ewma_lambda
    result = run_r_file("trend.R", data)
    output(result)
