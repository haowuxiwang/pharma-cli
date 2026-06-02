"""Equivalence tests command."""
import click

from cli.r_engine import run_r_file
from cli.commands.utils import output


@click.command()
@click.argument("test_type", type=click.Choice(["tost", "one_sample_tost"]))
@click.option("--x", multiple=True, type=float, help="First sample values")
@click.option("--y", multiple=True, type=float, help="Second sample values (for tost)")
@click.option("--mu", type=float, help="Hypothesized mean (for one_sample_tost)")
@click.option("--delta", type=float, required=True, help="Equivalence margin")
def equivalence(test_type, x, y, mu, delta):
    """Equivalence tests: tost, one_sample_tost."""
    if test_type == "tost":
        if not x or not y:
            raise click.UsageError("--x and --y required for two-sample TOST")
        data = {"test_type": test_type, "x": list(x), "y": list(y), "delta": delta}
    elif test_type == "one_sample_tost":
        if not x:
            raise click.UsageError("--x required for one-sample TOST")
        if mu is None:
            raise click.UsageError("--mu required for one-sample TOST")
        data = {"test_type": test_type, "x": list(x), "mu": mu, "delta": delta}

    result = run_r_file("equivalence.R", data)
    output(result)
