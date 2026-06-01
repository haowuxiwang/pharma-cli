"""Main CLI entry point using Click."""
import click
import json
import sys
import numpy as np
from pathlib import Path
from datetime import datetime

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
@click.version_option(version="0.3.0")
@click.option("--plot", "generate_plot", is_flag=True, default=False, help="Generate chart (base64 PNG)")
@click.option("--interactive", is_flag=True, default=False, help="Generate interactive HTML chart")
@click.option("--report", is_flag=True, default=False, help="Generate HTML report")
@click.pass_context
def main(ctx, generate_plot, interactive, report):
    """stats-cli: AI-friendly statistical analysis CLI for manufacturing."""
    ctx.ensure_object(dict)
    ctx.obj["generate_plot"] = generate_plot
    ctx.obj["interactive"] = interactive
    ctx.obj["report"] = report


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

    # Generate report if requested
    if ctx.obj.get("report"):
        from cli.reports import ReportGenerator
        from cli.charts import create_histogram
        generator = ReportGenerator()

        # Generate histogram if interactive
        chart = None
        if ctx.obj.get("interactive"):
            norm_data = run_r_file("normality.R", data)
            chart = create_histogram(norm_data, title="Data Distribution")

        html = generator.generate_descriptive_report(result, chart)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"descriptive_report_{timestamp}.html"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html)
        result['report_file'] = report_file

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

    # Generate interactive chart if requested
    if ctx.obj.get("interactive"):
        from cli.charts import create_histogram, create_qq_plot
        html_histogram = create_histogram(result, title="Normality Test - Histogram")
        html_qq = create_qq_plot(result)

        # Save charts
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        histogram_file = f"normality_histogram_{timestamp}.html"
        qq_file = f"normality_qq_{timestamp}.html"

        with open(histogram_file, 'w', encoding='utf-8') as f:
            f.write(html_histogram)
        with open(qq_file, 'w', encoding='utf-8') as f:
            f.write(html_qq)

        result['interactive_charts'] = {
            'histogram': histogram_file,
            'qq_plot': qq_file
        }

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

    # Generate interactive chart if requested
    if ctx.obj.get("interactive"):
        from cli.charts import create_capability_chart
        html = create_capability_chart(result)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        chart_file = f"capability_{timestamp}.html"
        with open(chart_file, 'w', encoding='utf-8') as f:
            f.write(html)
        result['interactive_chart'] = chart_file

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

    # Generate interactive chart if requested
    if ctx.obj.get("interactive"):
        from cli.charts import create_control_chart
        html = create_control_chart(result)
        chart_file = f"control_chart_{chart_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        with open(chart_file, 'w', encoding='utf-8') as f:
            f.write(html)
        result['interactive_chart'] = chart_file

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
@click.pass_context
def regression(ctx, x, y, data_file, x_column, y_column, reg_type, degree):
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

    # Generate interactive diagnostic plots if requested
    if ctx.obj.get("interactive"):
        from cli.charts import create_diagnostic_plots
        plots = create_diagnostic_plots(result)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        interactive_charts = {}
        for plot_name, html in plots.items():
            filename = f"regression_{plot_name}_{timestamp}.html"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html)
            interactive_charts[plot_name] = filename

        result['interactive_charts'] = interactive_charts

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
@click.argument("test_type", type=click.Choice(["mann_whitney", "kruskal_wallis", "wilcoxon"]))
@click.option("--x", multiple=True, type=float, help="First sample values")
@click.option("--y", multiple=True, type=float, help="Second sample values")
@click.option("--groups", "-g", multiple=True, help="Groups as JSON arrays (for kruskal_wallis)")
def nonparametric(test_type, x, y, groups):
    """Non-parametric tests: mann_whitney, kruskal_wallis, wilcoxon."""
    if test_type in ["mann_whitney", "wilcoxon"]:
        if not x or not y:
            raise click.UsageError("--x and --y required for this test")
        data = {"test_type": test_type, "x": list(x), "y": list(y)}
    elif test_type == "kruskal_wallis":
        if not groups:
            raise click.UsageError("--groups required for Kruskal-Wallis test")
        group_list = [json.loads(g) for g in groups]
        data = {"test_type": test_type, "groups": group_list}

    result = run_r_file("nonparametric.R", data)
    _output(result)


@main.command()
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

        # Support Excel files directly
        if path.suffix in [".xlsx", ".xls"]:
            try:
                import pandas as pd
                df = pd.read_excel(path)

                if column:
                    # Try to find column by name or index
                    col_found = False

                    # Try as column name (string match)
                    if column in df.columns:
                        values = df[column].dropna().tolist()
                        col_found = True

                    # Try as column name (numeric match)
                    if not col_found:
                        try:
                            col_num = float(column)
                            for col in df.columns:
                                if float(col) == col_num:
                                    values = df[col].dropna().tolist()
                                    col_found = True
                                    break
                        except (ValueError, TypeError):
                            pass

                    # Try as column index
                    if not col_found:
                        try:
                            col_idx = int(column)
                            if 0 <= col_idx < len(df.columns):
                                values = df.iloc[:, col_idx].dropna().tolist()
                                col_found = True
                        except (ValueError, IndexError):
                            pass

                    if not col_found:
                        raise click.UsageError(f"Column '{column}' not found in Excel file")
                else:
                    # Use first numeric column
                    numeric_cols = df.select_dtypes(include=[np.number]).columns
                    if len(numeric_cols) > 0:
                        values = df[numeric_cols[0]].dropna().tolist()
                    else:
                        raise click.UsageError("No numeric columns found in Excel file")

                return {"values": [float(v) for v in values]}
            except ImportError:
                raise click.UsageError("pandas is required to read Excel files. Install with: pip install pandas")

        # Read text-based files
        content = path.read_text(encoding="utf-8").strip()

        if path.suffix == ".csv":
            import csv
            import io
            reader = csv.DictReader(io.StringIO(content))
            if column:
                # Try to find column by name or index
                try:
                    values = [float(row[column]) for row in reader]
                except KeyError:
                    # Try as column index
                    try:
                        col_idx = int(column)
                        reader = csv.DictReader(io.StringIO(content))
                        values = [float(list(row.values())[col_idx]) for row in reader]
                    except (ValueError, IndexError):
                        raise click.UsageError(f"Column '{column}' not found in CSV file")
            else:
                # Use first numeric column
                first_row = next(reader)
                col_name = None
                for k, v in first_row.items():
                    try:
                        float(v)
                        col_name = k
                        break
                    except ValueError:
                        continue

                if col_name is None:
                    raise click.UsageError("No numeric columns found in CSV file")

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


@main.command()
@click.option("--values", "-v", multiple=True, type=float, help="Data values")
@click.option("--file", "-f", "data_file", type=click.Path(exists=True), help="File with data")
@click.option("--column", "-c", default=None, help="Column name if file is CSV/TSV")
@click.option("--usl", type=float, default=None, help="Upper specification limit")
@click.option("--lsl", type=float, default=None, help="Lower specification limit")
@click.pass_context
def report(ctx, values, data_file, column, usl, lsl):
    """Generate comprehensive analysis report."""
    data = _load_data(values, data_file, column)
    if "values" in data:
        validate_values(tuple(data["values"]), min_count=2, name="values")

    # Run all analyses
    analyses = {}
    charts = {}

    # Descriptive
    desc_result = run_r_file("descriptive.R", data)
    analyses['descriptive'] = desc_result

    # Normality
    norm_result = run_r_file("normality.R", data)
    analyses['normality'] = norm_result

    # Capability (if limits provided)
    if usl or lsl:
        cap_data = data.copy()
        cap_data['usl'] = usl
        cap_data['lsl'] = lsl
        cap_result = run_r_file("capability.R", cap_data)
        analyses['capability'] = cap_result

    # Control chart
    cc_data = data.copy()
    cc_data['chart_type'] = 'imr'
    cc_result = run_r_file("control_chart.R", cc_data)
    analyses['control_chart'] = cc_result

    # Generate charts if interactive mode
    if ctx.obj.get("interactive"):
        from cli.charts import create_histogram, create_control_chart, create_capability_chart

        # Histogram
        charts['histogram'] = create_histogram(norm_result, title="Data Distribution")

        # Control chart
        charts['control_chart'] = create_control_chart(cc_result)

        # Capability chart (if limits provided)
        if usl or lsl and 'capability' in analyses:
            charts['capability'] = create_capability_chart(analyses['capability'])

    # Generate report
    from cli.reports import ReportGenerator
    generator = ReportGenerator()

    if usl or lsl:
        html = generator.generate_comprehensive_report(analyses, charts)
    else:
        html = generator.generate_descriptive_report(desc_result, charts.get('histogram'))

    # Save report
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f"report_{timestamp}.html"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(html)

    _output({
        "report_file": report_file,
        "analyses": analyses,
        "message": f"Report generated: {report_file}"
    })


if __name__ == "__main__":
    main()
