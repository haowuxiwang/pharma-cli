"""Descriptive statistics command."""
import click
from datetime import datetime

from cli.r_engine import run_r_file
from cli.validators import validate_values
from cli.commands.utils import load_data, output


@click.command()
@click.option("--values", "-v", multiple=True, type=float, help="Data values (repeat for multiple)")
@click.option("--file", "-f", "data_file", type=click.Path(exists=True), help="File with data (one value per line)")
@click.option("--column", "-c", default=None, help="Column name if file is CSV/TSV")
@click.option("--json", "json_output", is_flag=True, default=True, help="Output as JSON (default)")
@click.pass_context
def descriptive(ctx, values, data_file, column, json_output):
    """Descriptive statistics: mean, median, SD, RSD%, range, quartiles, 95% CI."""
    data = load_data(values, data_file, column)
    if "values" in data:
        validate_values(tuple(data["values"]), min_count=1, name="values")
    if ctx.obj.get("generate_plot"):
        data["generate_plot"] = True
    result = run_r_file("descriptive.R", data)

    # Generate report if requested
    if ctx.obj.get("report"):
        from cli.reports import ReportGenerator
        from cli.charts import create_histogram
        generator = ReportGenerator()

        # Generate histogram if interactive
        chart = None
        if ctx.obj.get("interactive"):
            norm_data = run_r_file("normality.R", data)
            chart = create_histogram(norm_data, title="Data Distribution")

        html = generator.generate_descriptive_report(result, chart)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"descriptive_report_{timestamp}.html"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html)
        result['report_file'] = report_file

    output(result)
