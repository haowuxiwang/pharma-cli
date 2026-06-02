"""Non-parametric tests command."""
import json
import click

from cli.r_engine import run_r_file
from cli.commands.utils import output


@click.command()
@click.argument("test_type", type=click.Choice([
    "mann_whitney", "kruskal_wallis", "wilcoxon", "chi_square", "friedman"
]))
@click.option("--x", multiple=True, type=float, help="First sample values")
@click.option("--y", multiple=True, type=float, help="Second sample values")
@click.option("--groups", "-g", multiple=True, help="Groups as JSON arrays")
@click.option("--observed", multiple=True, type=float, help="Observed frequencies (chi-square)")
@click.option("--expected", multiple=True, type=float, help="Expected frequencies (chi-square)")
@click.option("--observed-matrix", default=None, help="Observed matrix as JSON (chi-square independence)")
@click.option("--chi-type", type=click.Choice(["goodness_of_fit", "independence"]), default="goodness_of_fit",
              help="Chi-square test type")
def nonparametric(test_type, x, y, groups, observed, expected, observed_matrix, chi_type):
    """Non-parametric tests: mann_whitney, kruskal_wallis, wilcoxon, chi_square, friedman.

    Examples:

    \b
    # Mann-Whitney U test
    stats-cli nonparametric mann_whitney --x 10.2 --x 10.5 --y 11.3 --y 11.5

    \b
    # Chi-square goodness of fit
    stats-cli nonparametric chi_square --observed 50 --observed 30 --observed 20

    \b
    # Chi-square test of independence
    stats-cli nonparametric chi_square --chi-type independence --observed-matrix '[[10,20],[30,40]]'

    \b
    # Friedman test
    stats-cli nonparametric friedman -g '[10,12,14]' -g '[11,13,15]' -g '[12,14,16]'
    """
    data = {"test_type": test_type}

    if test_type in ["mann_whitney", "wilcoxon"]:
        if not x or not y:
            raise click.UsageError("--x and --y required for this test")
        data["x"] = list(x)
        data["y"] = list(y)

    elif test_type == "kruskal_wallis":
        if not groups:
            raise click.UsageError("--groups required for Kruskal-Wallis test")
        data["groups"] = [json.loads(g) for g in groups]

    elif test_type == "chi_square":
        data["chi_type"] = chi_type
        if chi_type == "goodness_of_fit":
            if not observed:
                raise click.UsageError("--observed required for chi-square goodness of fit")
            data["observed"] = list(observed)
            if expected:
                data["expected"] = list(expected)
        elif chi_type == "independence":
            if not observed_matrix:
                raise click.UsageError("--observed-matrix required for chi-square independence test")
            data["observed"] = json.loads(observed_matrix)

    elif test_type == "friedman":
        if not groups:
            raise click.UsageError("--groups required for Friedman test")
        data["groups"] = [json.loads(g) for g in groups]

    result = run_r_file("nonparametric.R", data)
    output(result)
