"""Comprehensive analysis report command."""
import click
from datetime import datetime

from cli.r_engine import run_r_file
from cli.validators import validate_values
from cli.commands.utils import load_data, output


@click.command()
@click.option("--values", "-v", multiple=True, type=float, help="Data values")
@click.option("--file", "-f", "data_file", type=click.Path(exists=True), help="File with data")
@click.option("--column", "-c", default=None, help="Column name if file is CSV/TSV")
@click.option("--usl", type=float, default=None, help="Upper specification limit")
@click.option("--lsl", type=float, default=None, help="Lower specification limit")
@click.pass_context
def report(ctx, values, data_file, column, usl, lsl):
    """Generate comprehensive analysis report."""
    data = load_data(values, data_file, column)
    if "values" in data:
        validate_values(tuple(data["values"]), min_count=2, name="values")

    # Run all analyses
    analyses = {}
    charts = {}

    # Descriptive
    desc_result = run_r_file("descriptive.R", data)
    analyses['descriptive'] = desc_result

    # Normality
    norm_result = run_r_file("normality.R", data)
    analyses['normality'] = norm_result

    # Capability (if limits provided)
    if usl or lsl:
        cap_data = data.copy()
        cap_data['usl'] = usl
        cap_data['lsl'] = lsl
        cap_result = run_r_file("capability.R", cap_data)
        analyses['capability'] = cap_result

    # Control chart
    cc_data = data.copy()
    cc_data['chart_type'] = 'imr'
    cc_result = run_r_file("control_chart.R", cc_data)
    analyses['control_chart'] = cc_result

    # Generate charts if interactive mode
    if ctx.obj.get("interactive"):
        from cli.charts import create_histogram, create_control_chart, create_capability_chart

        # Histogram
        charts['histogram'] = create_histogram(norm_result, title="Data Distribution")

        # Control chart
        charts['control_chart'] = create_control_chart(cc_result)

        # Capability chart (if limits provided)
        if usl or lsl and 'capability' in analyses:
            charts['capability'] = create_capability_chart(analyses['capability'])

    # Generate report
    from cli.reports import ReportGenerator
    generator = ReportGenerator()

    if usl or lsl:
        html = generator.generate_comprehensive_report(analyses, charts)
    else:
        html = generator.generate_descriptive_report(desc_result, charts.get('histogram'))

    # Save report
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f"report_{timestamp}.html"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(html)

    output({
        "report_file": report_file,
        "analyses": analyses,
        "message": f"Report generated: {report_file}"
    })
