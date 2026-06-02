"""t-test command."""
import click

from cli.r_engine import run_r_file
from cli.validators import validate_values
from cli.commands.utils import load_data, output


@click.command()
@click.argument("test_type", type=click.Choice(["one_sample", "two_sample", "paired"]))
@click.option("--values", "-v", multiple=True, type=float, help="First sample values")
@click.option("--values2", "-v2", multiple=True, type=float, help="Second sample values (for two_sample/paired)")
@click.option("--file", "-f", "data_file", type=click.Path(exists=True), help="File with data")
@click.option("--column", "-c", default=None, help="Column name if file is CSV/TSV")
@click.option("--mu", type=float, default=None, help="Hypothesized mean (for one_sample)")
def ttest(test_type, values, values2, data_file, column, mu):
    """t-tests: one_sample, two_sample, paired."""
    data = load_data(values, data_file, column)
    if "values" in data:
        validate_values(tuple(data["values"]), min_count=2, name="values")
    data["test_type"] = test_type
    if values2:
        data["values2"] = list(values2)
    if mu is not None:
        data["mu"] = mu
    result = run_r_file("ttest.R", data)
    output(result)
