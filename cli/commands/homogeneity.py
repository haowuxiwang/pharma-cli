"""Homogeneity of variance tests command."""
import json
import click

from cli.r_engine import run_r_file
from cli.commands.utils import output


@click.command()
@click.argument("test_type", type=click.Choice(["levene", "bartlett"]))
@click.option("--groups", "-g", multiple=True, help="Groups as JSON arrays (e.g., '[1,2,3]' '[4,5,6]')")
def homogeneity(test_type, groups):
    """Homogeneity of variance tests: levene, bartlett."""
    if not groups:
        raise click.UsageError("--groups required for homogeneity tests")
    group_list = [json.loads(g) for g in groups]
    data = {"test_type": test_type, "groups": group_list}
    result = run_r_file("homogeneity.R", data)
    output(result)
