"""Time series analysis command."""
import json
import click

from cli.r_engine import run_r_file
from cli.commands.utils import load_data, output


@click.command()
@click.argument("analysis_type", type=click.Choice([
    "exp_smoothing", "arima", "decomposition", "acf"
]))
@click.option("--values", "-v", multiple=True, type=float, help="Time series values")
@click.option("--file", "-f", "data_file", type=click.Path(exists=True), help="File with time series data")
@click.option("--column", "-c", default=None, help="Column name in file")
@click.option("--frequency", type=int, default=1, help="Seasonal frequency (e.g., 12 for monthly)")
@click.option("--method", type=click.Choice(["auto", "holt_winters"]), default="auto",
              help="Exponential smoothing method")
@click.option("--order", multiple=True, type=int, help="ARIMA order (p, d, q)")
@click.option("--n-forecast", type=int, default=10, help="Number of periods to forecast")
@click.option("--max-lag", type=int, default=None, help="Maximum lag for ACF/PACF")
@click.option("--decomp-type", type=click.Choice(["additive", "multiplicative"]), default="additive",
              help="Decomposition type")
@click.pass_context
def timeseries(ctx, analysis_type, values, data_file, column, frequency, method,
               order, n_forecast, max_lag, decomp_type):
    """Time series analysis: exponential smoothing, ARIMA, decomposition, ACF/PACF.

    ANALYSIS_TYPE: exp_smoothing, arima, decomposition, acf

    Examples:

    \b
    # Exponential smoothing
    stats-cli timeseries exp_smoothing -v 10 -v 12 -v 11 -v 13 -v 14 --frequency 4

    \b
    # ARIMA with auto-detection
    stats-cli timeseries arima -f data.csv -c "sales" --n-forecast 12

    \b
    # Seasonal decomposition
    stats-cli timeseries decomposition -f data.xlsx -c "monthly_sales" --frequency 12

    \b
    # ACF/PACF analysis
    stats-cli timeseries acf -f data.csv -c "residuals" --max-lag 20
    """
    # Load data
    if values:
        data = {"values": list(values)}
    elif data_file:
        data = load_data(values, data_file, column)
    else:
        raise click.UsageError("--values or --file required")

    data["analysis_type"] = analysis_type

    if analysis_type == "exp_smoothing":
        data["frequency"] = frequency
        data["method"] = method
        data["n_forecast"] = n_forecast

    elif analysis_type == "arima":
        if order:
            if len(order) != 3:
                raise click.UsageError("--order must have exactly 3 values: p d q")
            data["order"] = list(order)
        data["n_forecast"] = n_forecast

    elif analysis_type == "decomposition":
        data["frequency"] = frequency
        data["type"] = decomp_type

    elif analysis_type == "acf":
        if max_lag:
            data["max_lag"] = max_lag

    result = run_r_file("timeseries.R", data)
    output(result)
