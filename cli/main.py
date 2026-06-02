"""Main CLI entry point using Click."""
import click

from cli.commands import (
    descriptive,
    normality,
    capability,
    control_chart,
    ttest,
    anova,
    regression,
    correlation,
    nonparametric,
    homogeneity,
    multiple_comparison,
    equivalence,
    outlier,
    trend,
    doe,
    run,
    report,
    gage_rr,
    clean,
    transform,
    discover,
    explore,
    reliability,
    multivariate,
    timeseries,
    power,
)


@click.group()
@click.version_option(version="0.3.0")
@click.option("--plot", "generate_plot", is_flag=True, default=False, help="Generate chart (base64 PNG)")
@click.option("--interactive", is_flag=True, default=False, help="Generate interactive HTML chart")
@click.option("--report", "generate_report", is_flag=True, default=False, help="Generate HTML report")
@click.pass_context
def main(ctx, generate_plot, interactive, generate_report):
    """stats-cli: AI-friendly statistical analysis CLI for manufacturing."""
    ctx.ensure_object(dict)
    ctx.obj["generate_plot"] = generate_plot
    ctx.obj["interactive"] = interactive
    ctx.obj["report"] = generate_report


# Register all commands
main.add_command(descriptive)
main.add_command(normality)
main.add_command(capability)
main.add_command(control_chart)
main.add_command(ttest)
main.add_command(anova)
main.add_command(regression)
main.add_command(correlation)
main.add_command(nonparametric)
main.add_command(homogeneity)
main.add_command(multiple_comparison)
main.add_command(equivalence)
main.add_command(outlier)
main.add_command(trend)
main.add_command(doe)
main.add_command(run)
main.add_command(report)
main.add_command(gage_rr)
main.add_command(clean)
main.add_command(transform)
main.add_command(discover)
main.add_command(explore)
main.add_command(reliability)
main.add_command(multivariate)
main.add_command(timeseries)
main.add_command(power)


if __name__ == "__main__":
    main()
