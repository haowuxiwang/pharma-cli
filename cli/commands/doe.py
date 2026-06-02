"""Design of Experiments command."""
import json
import sys
import click

from cli.r_engine import run_r_file
from cli.commands.utils import output


@click.command()
@click.argument("doe_type", type=click.Choice(["full_factorial", "fractional_factorial", "response_surface", "taguchi"]))
@click.option("--factors", "-f", multiple=True, help='Factor definitions as JSON (e.g., \'{"name":"Temp","levels":3}\')')
@click.option("--responses", "-r", "responses_json", default=None, help="Responses as JSON array")
def doe(doe_type, factors, responses_json):
    """Design of Experiments: full_factorial, fractional_factorial, response_surface, taguchi."""
    if not factors:
        click.echo("Error: --factors required", err=True)
        sys.exit(1)
    factor_list = [json.loads(f) for f in factors]
    data = {"doe_type": doe_type, "factors": factor_list}
    if responses_json:
        data["responses"] = json.loads(responses_json)
    result = run_r_file("doe.R", data)
    output(result)
