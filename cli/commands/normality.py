"""Normality test command."""
import click
from datetime import datetime

from cli.r_engine import run_r_file
from cli.commands.utils import load_data, output


@click.command()
@click.option("--values", "-v", multiple=True, type=float, help="Data values")
@click.option("--file", "-f", "data_file", type=click.Path(exists=True), help="File with data")
@click.option("--column", "-c", default=None, help="Column name if file is CSV/TSV")
@click.pass_context
def normality(ctx, values, data_file, column):
    """Normality tests: Shapiro-Wilk, Anderson-Darling, Lilliefors."""
    data = load_data(values, data_file, column)
    if ctx.obj.get("generate_plot"):
        data["generate_plot"] = True
    result = run_r_file("normality.R", data)

    # Generate interactive chart if requested
    charts = {}
    if ctx.obj.get("interactive"):
        from cli.charts import create_histogram, create_qq_plot
        html_histogram = create_histogram(result, title="Normality Test - Histogram")
        html_qq = create_qq_plot(result)

        # Save charts
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        histogram_file = f"normality_histogram_{timestamp}.html"
        qq_file = f"normality_qq_{timestamp}.html"

        with open(histogram_file, 'w', encoding='utf-8') as f:
            f.write(html_histogram)
        with open(qq_file, 'w', encoding='utf-8') as f:
            f.write(html_qq)

        result['interactive_charts'] = {
            'histogram': histogram_file,
            'qq_plot': qq_file
        }

    # Generate report if requested
    if ctx.obj.get("report"):
        from cli.reports import ReportGenerator
        generator = ReportGenerator()
        html = generator.generate_normality_report(result, charts)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"normality_report_{timestamp}.html"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html)
        result['report_file'] = report_file

    output(result)
