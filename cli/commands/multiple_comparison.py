"""Multiple comparison tests command."""
import json
import click

from cli.r_engine import run_r_file
from cli.commands.utils import output


@click.command("multiple-comparison")
@click.argument("test_type", type=click.Choice(["tukey", "bonferroni", "scheffe"]))
@click.option("--groups", "-g", multiple=True, help="Groups as JSON arrays (e.g., '[1,2,3]' '[4,5,6]')")
@click.option("--alpha", type=float, default=0.05, help="Significance level")
def multiple_comparison(test_type, groups, alpha):
    """Multiple comparison tests: tukey, bonferroni, scheffe."""
    if not groups:
        raise click.UsageError("--groups required for multiple comparison tests")
    group_list = [json.loads(g) for g in groups]
    data = {"test_type": test_type, "groups": group_list, "alpha": alpha}
    result = run_r_file("multiple_comparison.R", data)
    output(result)
