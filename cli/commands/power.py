"""Power analysis and sample size calculation command."""
import json
import click

from cli.r_engine import run_r_file
from cli.commands.utils import output


@click.command()
@click.argument("analysis_type", type=click.Choice([
    "t_test", "anova", "proportion", "effect_size"
]))
@click.option("--test-type", type=click.Choice(["one_sample", "two_sample", "paired"]), default="two_sample",
              help="t-test type")
@click.option("--effect-size", type=float, help="Effect size (Cohen's d or f)")
@click.option("--alpha", type=float, default=0.05, help="Significance level")
@click.option("--power", "desired_power", type=float, default=0.80, help="Desired power (0-1)")
@click.option("--n", type=int, default=None, help="Sample size (if calculating power)")
@click.option("--n-groups", type=int, default=2, help="Number of groups (for ANOVA)")
@click.option("--p0", type=float, help="Null proportion (for proportion test)")
@click.option("--p1", type=float, help="Alternative proportion (for proportion test)")
@click.option("--metric", type=click.Choice(["cohens_d", "cohens_f", "eta_squared"]), default="cohens_d",
              help="Effect size metric")
@click.option("--m1", type=float, help="Mean of group 1 (for Cohen's d)")
@click.option("--m2", type=float, help="Mean of group 2 (for Cohen's d)")
@click.option("--sd1", type=float, help="SD of group 1 (for Cohen's d)")
@click.option("--sd2", type=float, help="SD of group 2 (for Cohen's d)")
@click.option("--n1", type=int, help="Sample size of group 1 (for Cohen's d)")
@click.option("--n2", type=int, help="Sample size of group 2 (for Cohen's d)")
@click.option("--ss-effect", type=float, help="Sum of squares effect (for eta_squared)")
@click.option("--ss-total", type=float, help="Sum of squares total (for eta_squared)")
def power(analysis_type, test_type, effect_size, alpha, desired_power, n, n_groups,
          p0, p1, metric, m1, m2, sd1, sd2, n1, n2, ss_effect, ss_total):
    """Power analysis and sample size calculation.

    ANALYSIS_TYPE: t_test, anova, proportion, effect_size

    Examples:

    \b
    # Calculate sample size for t-test
    stats-cli power t_test --effect-size 0.5 --alpha 0.05 --power 0.80

    \b
    # Calculate power for given sample size
    stats-cli power t_test --effect-size 0.5 --n 30

    \b
    # ANOVA sample size
    stats-cli power anova --n-groups 3 --effect-size 0.25

    \b
    # Calculate Cohen's d
    stats-cli power effect_size --metric cohens_d --m1 10 --m2 12 --sd1 2 --sd2 2.5 --n1 30 --n2 30
    """
    data = {"analysis_type": analysis_type}

    if analysis_type == "t_test":
        data["test_type"] = test_type
        if effect_size is None:
            raise click.UsageError("--effect-size required for t-test power analysis")
        data["effect_size"] = effect_size
        data["alpha"] = alpha
        data["power"] = desired_power
        if n:
            data["n"] = n

    elif analysis_type == "anova":
        data["n_groups"] = n_groups
        if effect_size is None:
            raise click.UsageError("--effect-size required for ANOVA power analysis")
        data["effect_size"] = effect_size
        data["alpha"] = alpha
        data["power"] = desired_power
        if n:
            data["n"] = n

    elif analysis_type == "proportion":
        if p0 is None or p1 is None:
            raise click.UsageError("--p0 and --p1 required for proportion power analysis")
        data["p0"] = p0
        data["p1"] = p1
        data["alpha"] = alpha
        data["power"] = desired_power

    elif analysis_type == "effect_size":
        data["metric"] = metric
        if metric == "cohens_d":
            if any(v is None for v in [m1, m2, sd1, sd2, n1, n2]):
                raise click.UsageError("--m1, --m2, --sd1, --sd2, --n1, --n2 required for Cohen's d")
            data.update({"m1": m1, "m2": m2, "sd1": sd1, "sd2": sd2, "n1": n1, "n2": n2})
        elif metric == "eta_squared":
            if ss_effect is None or ss_total is None:
                raise click.UsageError("--ss-effect and --ss-total required for eta-squared")
            data.update({"ss_effect": ss_effect, "ss_total": ss_total})

    result = run_r_file("power.R", data)
    output(result)
