"""ANOVA command."""
import json
import click

from cli.r_engine import run_r_file
from cli.validators import validate_groups
from cli.commands.utils import output


@click.command()
@click.argument("anova_type", type=click.Choice(["one_way", "two_way"]))
@click.option("--groups", "-g", multiple=True, help="Groups as JSON arrays (e.g., '[1,2,3]' '[4,5,6]')")
@click.option("--data", "-d", "data_json", default=None, help="JSON data for two-way ANOVA")
@click.option("--response", default=None, help="Response column name (for two_way)")
@click.option("--factor1", default=None, help="Factor 1 column name (for two_way)")
@click.option("--factor2", default=None, help="Factor 2 column name (for two_way)")
def anova(anova_type, groups, data_json, response, factor1, factor2):
    """ANOVA: one_way, two_way."""
    if anova_type == "one_way":
        group_list = validate_groups(groups, min_count=2)
        data = {"groups": group_list}
    else:
        if not data_json:
            raise click.UsageError("--data required for two-way ANOVA")
        data = json.loads(data_json)
        data["anova_type"] = "two_way"
        data["response"] = response
        data["factor1"] = factor1
        data["factor2"] = factor2
    result = run_r_file("anova.R", data)
    output(result)
