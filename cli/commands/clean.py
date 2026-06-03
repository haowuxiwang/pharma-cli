"""Data cleaning command."""
import click

from cli.r_engine import run_r_file
from cli.commands.utils import load_data, output


@click.command()
@click.option("--values", "-v", multiple=True, type=float, help="Data values")
@click.option("--file", "-f", "data_file", type=click.Path(exists=True), help="File with data")
@click.option("--column", "-c", default=None, help="Column name if file is CSV/TSV")
@click.option("--sheet", "-s", default=None, help="Excel sheet name (default: first sheet)")
@click.option("--method", type=click.Choice(["drop", "impute_mean", "impute_median", "winsorize", "clip"]),
              default="drop", help="Cleaning method")
@click.option("--lower-pct", type=float, default=0.05, help="Lower percentile for winsorize (0-1)")
@click.option("--upper-pct", type=float, default=0.95, help="Upper percentile for winsorize (0-1)")
@click.option("--lower", type=float, default=None, help="Lower bound for clip")
@click.option("--upper", type=float, default=None, help="Upper bound for clip")
def clean(values, data_file, column, sheet, method, lower_pct, upper_pct, lower, upper):
    """Clean data: handle missing values, outliers, and extreme values.

    Methods:

    \b
    - drop: Remove NA/NaN/Inf values
    - impute_mean: Replace missing with mean
    - impute_median: Replace missing with median
    - winsorize: Cap outliers at percentiles
    - clip: Clip values to specified range

    Examples:

    \b
    # Drop missing values
    stats-cli clean -f data.csv -c "weight" --method drop

    \b
    # Impute missing with mean
    stats-cli clean -v 10.1 -v NaN -v 10.3 --method impute_mean

    \b
    # Winsorize outliers at 5th/95th percentiles
    stats-cli clean -f data.xlsx -c "weight" --method winsorize --lower-pct 0.05 --upper-pct 0.95
    """
    data = load_data(values, data_file, column, sheet)
    data["method"] = method

    if method == "winsorize":
        data["lower_pct"] = lower_pct
        data["upper_pct"] = upper_pct
    elif method == "clip":
        if lower is None and upper is None:
            raise click.UsageError("Clip method requires --lower and/or --upper bounds")
        if lower is not None:
            data["lower"] = lower
        if upper is not None:
            data["upper"] = upper

    result = run_r_file("clean.R", data)
    output(result)
