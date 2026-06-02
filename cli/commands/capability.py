"""Process capability analysis command."""
import click
from datetime import datetime

from cli.r_engine import run_r_file
from cli.validators import validate_values, validate_spec_limits
from cli.commands.utils import load_data, output


@click.command()
@click.option("--values", "-v", multiple=True, type=float, help="Data values")
@click.option("--file", "-f", "data_file", type=click.Path(exists=True), help="File with data")
@click.option("--column", "-c", default=None, help="Column name if file is CSV/TSV")
@click.option("--sheet", "-s", default=None, help="Excel sheet name (default: first sheet)")
@click.option("--usl", type=float, default=None, help="Upper specification limit")
@click.option("--lsl", type=float, default=None, help="Lower specification limit")
@click.option("--target", type=float, default=None, help="Target value (default: midpoint of USL/LSL)")
@click.option("--type", "capability_type", type=click.Choice(["normal", "boxcox"]), default="normal",
              help="Capability analysis type (normal or boxcox for non-normal data)")
@click.pass_context
def capability(ctx, values, data_file, column, sheet, usl, lsl, target, capability_type):
    """Process capability analysis: Cp, Cpk, Pp, Ppk, Cpm.

    Includes:
    - Within-subgroup sigma (moving range method)
    - Cp/Cpk confidence intervals (95%)
    - Cpm (Taguchi capability index)
    - PPM defect rate and yield
    - Box-Cox capability for non-normal data (with --type boxcox)

    Examples:

    \b
    # Basic capability
    stats-cli capability -f data.csv -c "weight" --usl 11.0 --lsl 9.0

    \b
    # Non-normal capability with Box-Cox
    stats-cli capability -f data.xlsx -c "yield" --usl 100 --type boxcox
    """
    usl, lsl = validate_spec_limits(usl, lsl)
    data = load_data(values, data_file, column, sheet)
    if "values" in data:
        validate_values(tuple(data["values"]), min_count=2, name="values")
    data["usl"] = usl
    data["lsl"] = lsl
    data["target"] = target
    data["capability_type"] = capability_type
    if ctx.obj.get("generate_plot"):
        data["generate_plot"] = True
    result = run_r_file("capability.R", data)

    # Generate interactive chart if requested
    chart = None
    if ctx.obj.get("interactive"):
        from cli.charts import create_capability_chart
        html = create_capability_chart(result)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        chart_file = f"capability_{timestamp}.html"
        with open(chart_file, 'w', encoding='utf-8') as f:
            f.write(html)
        result['interactive_chart'] = chart_file
        chart = html

    # Generate report if requested
    if ctx.obj.get("report"):
        from cli.reports import ReportGenerator
        generator = ReportGenerator()
        html = generator.generate_capability_report(result, chart)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"capability_report_{timestamp}.html"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html)
        result['report_file'] = report_file

    output(result)
