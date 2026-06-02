"""Reliability analysis command."""
import json
import click

from cli.r_engine import run_r_file
from cli.commands.utils import output


@click.command()
@click.argument("analysis_type", type=click.Choice([
    "weibull", "kaplan_meier", "distribution", "stability"
]))
@click.option("--times", "-t", multiple=True, type=float, help="Time-to-failure values")
@click.option("--status", "-s", multiple=True, type=int, help="Status (1=failure, 0=censored)")
@click.option("--values", "-v", multiple=True, type=float, help="Measurement values (for stability)")
@click.option("--file", "-f", "data_file", type=click.Path(exists=True), help="JSON file with reliability data")
@click.option("--time", type=float, default=None, help="Time point for reliability calculation")
@click.option("--usl", type=float, default=None, help="Upper spec limit (for stability)")
@click.option("--lsl", type=float, default=None, help="Lower spec limit (for stability)")
@click.option("--confidence", type=float, default=0.95, help="Confidence level (0-1)")
@click.pass_context
def reliability(ctx, analysis_type, times, status, values, data_file, time, usl, lsl, confidence):
    """Reliability and survival analysis.

    ANALYSIS_TYPE: weibull, kaplan_meier, distribution, stability

    Examples:

    \b
    # Weibull analysis
    stats-cli reliability weibull -t 100 -t 200 -t 300 -t 150 -t 250 -s 1 -s 1 -s 1 -s 0 -s 1

    \b
    # Stability study (shelf life)
    stats-cli reliability stability -t 0 -t 3 -t 6 -t 9 -t 12 -t 24 -v 100 -v 99 -v 98 -v 97 -v 96 -v 94 --lsl 90

    \b
    # From JSON file
    stats-cli reliability weibull -f reliability_data.json --time 500
    """
    if data_file:
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        data['analysis_type'] = analysis_type
    else:
        data = {'analysis_type': analysis_type}

        if analysis_type == "weibull":
            if not times or not status:
                raise click.UsageError("Weibull requires --times and --status")
            if len(times) != len(status):
                raise click.UsageError("--times and --status must have same length")
            data['times'] = list(times)
            data['status'] = list(status)
            if time is not None:
                data['time'] = time

        elif analysis_type == "kaplan_meier":
            if not times or not status:
                raise click.UsageError("Kaplan-Meier requires --times and --status")
            data['times'] = list(times)
            data['status'] = list(status)

        elif analysis_type == "distribution":
            if not times or not status:
                raise click.UsageError("Distribution fitting requires --times and --status")
            data['times'] = list(times)
            data['status'] = list(status)

        elif analysis_type == "stability":
            if not times or not values:
                raise click.UsageError("Stability requires --times and --values")
            if len(times) != len(values):
                raise click.UsageError("--times and --values must have same length")
            data['times'] = list(times)
            data['values'] = list(values)
            if usl is not None:
                data['usl'] = usl
            if lsl is not None:
                data['lsl'] = lsl
            data['confidence'] = confidence

    result = run_r_file("reliability.R", data)
    output(result)
