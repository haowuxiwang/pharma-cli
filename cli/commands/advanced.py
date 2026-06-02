"""Advanced statistical methods command."""
import json
import click

from cli.r_engine import run_r_file
from cli.commands.utils import output


@click.command()
@click.argument("analysis_type", type=click.Choice([
    "mixed_effects", "cox_regression", "exact_test", "friedman", "mcnemar", "cochran_q"
]))
@click.option("--file", "-f", "data_file", type=click.Path(exists=True), help="JSON file with data")
@click.option("--response", default=None, help="Response column (for mixed_effects)")
@click.option("--fixed-effects", multiple=True, help="Fixed effect columns (for mixed_effects)")
@click.option("--random-effects", multiple=True, help="Random effect columns (for mixed_effects)")
@click.option("--time-column", default=None, help="Time column (for cox_regression)")
@click.option("--status-column", default=None, help="Status column (for cox_regression)")
@click.option("--covariates", multiple=True, help="Covariate columns (for cox_regression)")
@click.option("--observed-matrix", default=None, help="Observed matrix as JSON (for exact_test/mcnemar)")
@click.option("--groups", "-g", multiple=True, help="Groups as JSON arrays (for friedman)")
@click.option("--data-matrix", default=None, help="Data matrix as JSON (for cochran_q)")
def advanced(analysis_type, data_file, response, fixed_effects, random_effects,
             time_column, status_column, covariates, observed_matrix, groups, data_matrix):
    """Advanced statistical methods: mixed effects, Cox regression, exact tests.

    ANALYSIS_TYPE: mixed_effects, cox_regression, exact_test, friedman, mcnemar, cochran_q

    Examples:

    \b
    # Mixed effects model
    stats-cli advanced mixed_effects -f data.json --response "y" --fixed-effects "x1" --fixed-effects "x2" --random-effects "subject"

    \b
    # Cox regression
    stats-cli advanced cox_regression -f data.json --time-column "time" --status-column "status" --covariates "treatment"

    \b
    # Fisher's exact test
    stats-cli advanced exact_test --observed-matrix '[[10,20],[30,40]]'

    \b
    # McNemar's test
    stats-cli advanced mcnemar --observed-matrix '[[10,5],[15,20]]'
    """
    data = {"analysis_type": analysis_type}

    if data_file:
        with open(data_file, 'r', encoding='utf-8') as f:
            file_data = json.load(f)
        data.update(file_data)

    if analysis_type == "mixed_effects":
        if not response or not fixed_effects:
            raise click.UsageError("--response and --fixed-effects required")
        data["response"] = response
        data["fixed_effects"] = list(fixed_effects)
        data["random_effects"] = list(random_effects) if random_effects else list(fixed_effects)

    elif analysis_type == "cox_regression":
        if not time_column or not status_column:
            raise click.UsageError("--time-column and --status-column required")
        data["time_column"] = time_column
        data["status_column"] = status_column
        data["covariates"] = list(covariates) if covariates else []

    elif analysis_type in ["exact_test", "mcnemar"]:
        if not observed_matrix:
            raise click.UsageError("--observed-matrix required")
        data["observed"] = json.loads(observed_matrix)

    elif analysis_type == "friedman":
        if not groups:
            raise click.UsageError("--groups required")
        data["groups"] = [json.loads(g) for g in groups]

    elif analysis_type == "cochran_q":
        if not data_matrix:
            raise click.UsageError("--data-matrix required")
        data["data"] = json.loads(data_matrix)

    result = run_r_file("advanced.R", data)
    output(result)
