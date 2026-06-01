"""Main CLI entry point using Click."""
import click
import json
import sys
from pathlib import Path

from cli.r_engine import run_r_file
from cli.validators import (
    validate_values,
    validate_spec_limits,
    validate_groups,
    validate_xy,
    validate_alpha,
    validate_subgroup_size,
)


@click.group()
@click.version_option(version="0.2.0")
@click.option("--plot", "generate_plot", is_flag=True, default=False, help="Generate chart (base64 PNG)")
@click.pass_context
def main(ctx, generate_plot):
    """pharma-cli: AI-agent-friendly statistical analysis powered by R."""
    ctx.ensure_object(dict)
    ctx.obj["generate_plot"] = generate_plot


@main.command()
@click.option("--values", "-v", multiple=True, type=float, help="Data values (repeat for multiple)")
@click.option("--file", "-f", "data_file", type=click.Path(exists=True), help="File with data (one value per line)")
@click.option("--column", "-c", default=None, help="Column name if file is CSV/TSV")
@click.option("--json", "json_output", is_flag=True, default=True, help="Output as JSON (default)")
@click.pass_context
def descriptive(ctx, values, data_file, column, json_output):
    """Descriptive statistics: mean, median, SD, RSD%, range, quartiles, 95% CI."""
    data = _load_data(values, data_file, column)
    if "values" in data:
        validate_values(tuple(data["values"]), min_count=1, name="values")
    if ctx.obj.get("generate_plot"):
        data["generate_plot"] = True
    result = run_r_file("descriptive.R", data)
    _output(result)


@main.command()
@click.option("--values", "-v", multiple=True, type=float, help="Data values")
@click.option("--file", "-f", "data_file", type=click.Path(exists=True), help="File with data")
@click.option("--column", "-c", default=None, help="Column name if file is CSV/TSV")
@click.pass_context
def normality(ctx, values, data_file, column):
    """Normality tests: Shapiro-Wilk, Anderson-Darling, Lilliefors."""
    data = _load_data(values, data_file, column)
    if ctx.obj.get("generate_plot"):
        data["generate_plot"] = True
    result = run_r_file("normality.R", data)
    _output(result)


@main.command()
@click.option("--values", "-v", multiple=True, type=float, help="Data values")
@click.option("--file", "-f", "data_file", type=click.Path(exists=True), help="File with data")
@click.option("--column", "-c", default=None, help="Column name if file is CSV/TSV")
@click.option("--usl", type=float, default=None, help="Upper specification limit")
@click.option("--lsl", type=float, default=None, help="Lower specification limit")
@click.option("--target", type=float, default=None, help="Target value (default: midpoint of USL/LSL)")
@click.pass_context
def capability(ctx, values, data_file, column, usl, lsl, target):
    """Process capability analysis: Cp, Cpk, Pp, Ppk."""
    usl, lsl = validate_spec_limits(usl, lsl)
    data = _load_data(values, data_file, column)
    if "values" in data:
        validate_values(tuple(data["values"]), min_count=2, name="values")
    data["usl"] = usl
    data["lsl"] = lsl
    data["target"] = target
    if ctx.obj.get("generate_plot"):
        data["generate_plot"] = True
    result = run_r_file("capability.R", data)
    _output(result)


@main.command()
@click.argument("chart_type", type=click.Choice(["xbar", "r", "imr", "p", "np", "c", "u"]))
@click.option("--values", "-v", multiple=True, type=float, help="Data values")
@click.option("--file", "-f", "data_file", type=click.Path(exists=True), help="File with data")
@click.option("--column", "-c", default=None, help="Column name if file is CSV/TSV")
@click.option("--subgroup-size", "-s", default=5, type=int, help="Subgroup size (default 5)")
@click.option("--sample-size", default=None, type=int, help="Sample size for p/np/c/u charts")
@click.pass_context
def control_chart(ctx, chart_type, values, data_file, column, subgroup_size, sample_size):
    """Control charts: xbar, r, imr, p, np, c, u with Western Electric rules."""
    subgroup_size = validate_subgroup_size(subgroup_size)
    data = _load_data(values, data_file, column)
    if "values" in data:
        validate_values(tuple(data["values"]), min_count=2, name="values")
    data["chart_type"] = chart_type
    data["subgroup_size"] = subgroup_size
    if sample_size:
        data["sample_size"] = sample_size
    if ctx.obj.get("generate_plot"):
        data["generate_plot"] = True
    result = run_r_file("control_chart.R", data)
    _output(result)


@main.command()
@click.argument("test_type", type=click.Choice(["one_sample", "two_sample", "paired"]))
@click.option("--values", "-v", multiple=True, type=float, help="First sample values")
@click.option("--values2", "-v2", multiple=True, type=float, help="Second sample values (for two_sample/paired)")
@click.option("--file", "-f", "data_file", type=click.Path(exists=True), help="File with data")
@click.option("--column", "-c", default=None, help="Column name if file is CSV/TSV")
@click.option("--mu", type=float, default=None, help="Hypothesized mean (for one_sample)")
def ttest(test_type, values, values2, data_file, column, mu):
    """t-tests: one_sample, two_sample, paired."""
    data = _load_data(values, data_file, column)
    if "values" in data:
        validate_values(tuple(data["values"]), min_count=2, name="values")
    data["test_type"] = test_type
    if values2:
        data["values2"] = list(values2)
    if mu is not None:
        data["mu"] = mu
    result = run_r_file("ttest.R", data)
    _output(result)


@main.command()
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
    _output(result)


@main.command()
@click.option("--x", multiple=True, type=float, help="Independent variable values")
@click.option("--y", multiple=True, type=float, help="Dependent variable values")
@click.option("--file", "-f", "data_file", type=click.Path(exists=True), help="File with data")
@click.option("--x-column", default=None, help="X column name in CSV")
@click.option("--y-column", default=None, help="Y column name in CSV")
@click.option("--type", "reg_type", type=click.Choice(["linear", "quadratic", "polynomial"]), default="linear")
@click.option("--degree", type=int, default=3, help="Polynomial degree (for polynomial type)")
def regression(x, y, data_file, x_column, y_column, reg_type, degree):
    """Regression analysis: linear, quadratic, polynomial."""
    if x and y:
        x_list, y_list = validate_xy(x, y)
        data = {"x": x_list, "y": y_list}
    elif data_file:
        path = Path(data_file)
        content = path.read_text(encoding="utf-8").strip()
        if path.suffix == ".csv":
            import csv, io
            reader = csv.DictReader(io.StringIO(content))
            rows = list(reader)
            x_col = x_column or "x"
            y_col = y_column or "y"
            data = {
                "x": [float(r[x_col]) for r in rows],
                "y": [float(r[y_col]) for r in rows]
            }
        else:
            lines = content.splitlines()
            pairs = [line.split() for line in lines if line.strip()]
            data = {"x": [float(p[0]) for p in pairs], "y": [float(p[1]) for p in pairs]}
    else:
        raise click.UsageError("provide --x/--y or --file")
    data["reg_type"] = reg_type
    data["degree"] = degree
    result = run_r_file("regression.R", data)
    _output(result)


@main.command()
@click.option("--x", multiple=True, type=float, help="First variable values")
@click.option("--y", multiple=True, type=float, help="Second variable values")
@click.option("--file", "-f", "data_file", type=click.Path(exists=True), help="File with data")
@click.option("--method", type=click.Choice(["pearson", "spearman", "kendall"]), default="pearson")
def correlation(x, y, data_file, method):
    """Correlation analysis: pearson, spearman, kendall."""
    if x and y:
        x_list, y_list = validate_xy(x, y)
        data = {"x": x_list, "y": y_list}
    elif data_file:
        path = Path(data_file)
        content = path.read_text(encoding="utf-8").strip()
        if path.suffix == ".json":
            data = json.loads(content)
        else:
            lines = content.splitlines()
            pairs = [line.split() for line in lines if line.strip()]
            data = {"x": [float(p[0]) for p in pairs], "y": [float(p[1]) for p in pairs]}
    else:
        raise click.UsageError("provide --x/--y or --file")
    data["method"] = method
    result = run_r_file("correlation.R", data)
    _output(result)


@main.command()
@click.option("--values", "-v", multiple=True, type=float, help="Data values")
@click.option("--file", "-f", "data_file", type=click.Path(exists=True), help="File with data")
@click.option("--column", "-c", default=None, help="Column name if file is CSV/TSV")
@click.option("--method", type=click.Choice(["grubbs", "dixon", "iqr", "zscore"]), default="grubbs")
@click.option("--alpha", type=float, default=0.05, help="Significance level")
def outlier(values, data_file, column, method, alpha):
    """Outlier detection: grubbs, dixon, iqr, zscore."""
    alpha = validate_alpha(alpha)
    data = _load_data(values, data_file, column)
    if "values" in data:
        validate_values(tuple(data["values"]), min_count=3, name="values")
    data["method"] = method
    data["alpha"] = alpha
    result = run_r_file("outlier.R", data)
    _output(result)


@main.command()
@click.option("--values", "-v", multiple=True, type=float, help="Data values")
@click.option("--file", "-f", "data_file", type=click.Path(exists=True), help="File with data")
@click.option("--column", "-c", default=None, help="Column name if file is CSV/TSV")
@click.option("--test-type", type=click.Choice(["cusum", "ewma", "runs"]), default="cusum")
@click.option("--target", type=float, default=None, help="Target value (for cusum/ewma)")
@click.option("--ewma-lambda", type=float, default=0.2, help="EWMA lambda parameter")
def trend(values, data_file, column, test_type, target, ewma_lambda):
    """Trend analysis: cusum, ewma, runs test."""
    data = _load_data(values, data_file, column)
    data["test_type"] = test_type
    if target is not None:
        data["target"] = target
    data["lambda"] = ewma_lambda
    result = run_r_file("trend.R", data)
    _output(result)


@main.command()
@click.argument("doe_type", type=click.Choice(["full_factorial", "fractional_factorial", "response_surface"]))
@click.option("--factors", "-f", multiple=True, help='Factor definitions as JSON (e.g., \'{"name":"Temp","levels":3}\')')
@click.option("--responses", "-r", "responses_json", default=None, help="Responses as JSON array")
def doe(doe_type, factors, responses_json):
    """Design of Experiments: full_factorial, fractional_factorial, response_surface."""
    if not factors:
        click.echo("Error: --factors required", err=True)
        sys.exit(1)
    factor_list = [json.loads(f) for f in factors]
    data = {"doe_type": doe_type, "factors": factor_list}
    if responses_json:
        data["responses"] = json.loads(responses_json)
    result = run_r_file("doe.R", data)
    _output(result)


@main.command()
@click.argument("script_name")
@click.option("--data", "-d", default=None, help="JSON string of data to pass to R script")
def run(script_name, data):
    """Run a custom R script from the r_scripts directory."""
    data_dict = json.loads(data) if data else None
    result = run_r_file(script_name, data_dict)
    _output(result)


def _load_data(values, data_file, column):
    """Load data from CLI arguments or file."""
    if values:
        return {"values": list(values)}
    elif data_file:
        path = Path(data_file)
        content = path.read_text(encoding="utf-8").strip()
        if path.suffix == ".csv":
            import csv
            import io
            reader = csv.DictReader(io.StringIO(content))
            if column:
                values = [float(row[column]) for row in reader]
            else:
                # Use first numeric column
                first_row = next(reader)
                for k, v in first_row.items():
                    try:
                        float(v)
                        col_name = k
                        break
                    except ValueError:
                        continue
                reader = csv.DictReader(io.StringIO(content))
                values = [float(row[col_name]) for row in reader]
            return {"values": values}
        elif path.suffix == ".json":
            return json.loads(content)
        else:
            # Plain text, one value per line
            values = [float(line) for line in content.splitlines() if line.strip()]
            return {"values": values}
    else:
        # Read from stdin
        content = sys.stdin.read().strip()
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            values = [float(line) for line in content.splitlines() if line.strip()]
            return {"values": values}


def _output(data):
    """Output result as JSON."""
    click.echo(json.dumps(data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
