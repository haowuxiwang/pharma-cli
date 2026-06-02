"""Control chart command."""
import click
from datetime import datetime

from cli.r_engine import run_r_file
from cli.validators import validate_values, validate_subgroup_size
from cli.commands.utils import load_data, output


@click.command("control-chart")
@click.argument("chart_type", type=click.Choice(["xbar", "r", "imr", "p", "np", "c", "u", "ewma", "cusum"]))
@click.option("--values", "-v", multiple=True, type=float, help="Data values")
@click.option("--file", "-f", "data_file", type=click.Path(exists=True), help="File with data")
@click.option("--column", "-c", default=None, help="Column name if file is CSV/TSV")
@click.option("--sheet", default=None, help="Excel sheet name (default: first sheet)")
@click.option("--subgroup-size", "-s", default=5, type=int, help="Subgroup size (default 5)")
@click.option("--sample-size", default=None, type=int, help="Sample size for p/np/c/u charts")
@click.option("--target", type=float, default=None, help="Target value (for ewma/cusum)")
@click.option("--ewma-lambda", type=float, default=0.2, help="EWMA lambda parameter (0-1)")
@click.option("--cusum-k", type=float, default=0.5, help="CUSUM reference value (k * sigma)")
@click.option("--cusum-h", type=float, default=5, help="CUSUM decision interval (h * sigma)")
@click.pass_context
def control_chart(ctx, chart_type, values, data_file, column, sheet, subgroup_size, sample_size, target, ewma_lambda, cusum_k, cusum_h):
    """Control charts: xbar, r, imr, p, np, c, u, ewma, cusum with Western Electric rules."""
    subgroup_size = validate_subgroup_size(subgroup_size)
    data = load_data(values, data_file, column, sheet)
    if "values" in data:
        validate_values(tuple(data["values"]), min_count=2, name="values")
    data["chart_type"] = chart_type
    data["subgroup_size"] = subgroup_size
    if sample_size:
        data["sample_size"] = sample_size
    if target is not None:
        data["target"] = target
    if ewma_lambda:
        data["lambda"] = ewma_lambda
    if cusum_k:
        data["k"] = cusum_k
    if cusum_h:
        data["h"] = cusum_h
    if ctx.obj.get("generate_plot"):
        data["generate_plot"] = True
    result = run_r_file("control_chart.R", data)

    # Generate interactive chart if requested
    if ctx.obj.get("interactive"):
        from cli.charts import create_control_chart
        html = create_control_chart(result)
        chart_file = f"control_chart_{chart_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        with open(chart_file, 'w', encoding='utf-8') as f:
            f.write(html)
        result['interactive_chart'] = chart_file

    output(result)
