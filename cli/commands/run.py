"""Run custom R script command."""
import json
import click

from cli.r_engine import run_r_file
from cli.commands.utils import output


@click.command()
@click.argument("script_name")
@click.option("--data", "-d", default=None, help="JSON string of data to pass to R script")
def run(script_name, data):
    """Run a custom R script from the r_scripts directory."""
    data_dict = json.loads(data) if data else None
    result = run_r_file(script_name, data_dict)
    output(result)
