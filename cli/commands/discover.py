"""Discover command - list all available commands and their schemas."""
import json
import click

from cli.commands.utils import output


# Command metadata
COMMANDS = {
    "descriptive": {
        "description": "Descriptive statistics: mean, median, SD, RSD%, range, quartiles, 95% CI",
        "category": "basic",
        "input": ["values", "file"],
        "output_fields": ["n", "mean", "median", "std", "rsd_percent", "min", "max", "range", "q1", "q3", "iqr", "ci_95_lower", "ci_95_upper", "skewness", "kurtosis"],
        "example": "stats-cli descriptive -f data.csv -c weight"
    },
    "normality": {
        "description": "Normality tests: Shapiro-Wilk, Anderson-Darling, Lilliefors",
        "category": "basic",
        "input": ["values", "file"],
        "output_fields": ["shapiro_wilk", "anderson_darling", "lilliefors", "is_normal"],
        "example": "stats-cli normality -f data.csv -c weight"
    },
    "capability": {
        "description": "Process capability: Cp, Cpk, Pp, Ppk, Cpm, confidence intervals",
        "category": "spc",
        "input": ["values", "file", "usl", "lsl", "target"],
        "output_fields": ["cp", "cpk", "pp", "ppk", "cpm", "cp_ci_lower", "cp_ci_upper", "cpk_ci_lower", "cpk_ci_upper", "rating", "performance"],
        "example": "stats-cli capability -f data.csv -c weight --usl 11.0 --lsl 9.0"
    },
    "control-chart": {
        "description": "Control charts: xbar, r, imr, p, np, c, u, ewma, cusum",
        "category": "spc",
        "input": ["values", "file", "chart_type", "subgroup_size"],
        "output_fields": ["chart_type", "center", "ucl", "lcl", "points", "out_of_control", "summary"],
        "example": "stats-cli control-chart imr -f data.csv -c weight"
    },
    "ttest": {
        "description": "t-tests: one_sample, two_sample, paired",
        "category": "hypothesis",
        "input": ["values", "values2", "test_type", "mu"],
        "output_fields": ["test_type", "t_statistic", "p_value", "significant", "ci_95"],
        "example": "stats-cli ttest two_sample -v 10.2 -v 10.5 -v2 11.3 -v2 11.5"
    },
    "anova": {
        "description": "ANOVA: one_way, two_way",
        "category": "hypothesis",
        "input": ["groups", "anova_type"],
        "output_fields": ["anova_type", "f_statistic", "p_value", "significant", "eta_squared"],
        "example": "stats-cli anova one_way -g '[10.2,10.5]' -g '[11.3,11.5]'"
    },
    "regression": {
        "description": "Regression: linear, quadratic, polynomial",
        "category": "regression",
        "input": ["x", "y", "file", "reg_type", "degree"],
        "output_fields": ["regression_type", "r_squared", "adj_r_squared", "coefficients", "f_statistic", "p_value"],
        "example": "stats-cli regression --x 1 --x 2 --x 3 --y 2 --y 4 --y 6"
    },
    "correlation": {
        "description": "Correlation: pearson, spearman, kendall",
        "category": "regression",
        "input": ["x", "y", "file", "method"],
        "output_fields": ["method", "correlation", "p_value", "r_squared"],
        "example": "stats-cli correlation --x 1 --x 2 --x 3 --y 2 --y 4 --y 6"
    },
    "nonparametric": {
        "description": "Non-parametric tests: mann_whitney, kruskal_wallis, wilcoxon",
        "category": "hypothesis",
        "input": ["x", "y", "groups", "test_type"],
        "output_fields": ["test_type", "statistic", "p_value", "significant"],
        "example": "stats-cli nonparametric mann_whitney --x 10.2 --x 10.5 --y 11.3 --y 11.5"
    },
    "homogeneity": {
        "description": "Homogeneity of variance: levene, bartlett",
        "category": "hypothesis",
        "input": ["groups", "test_type"],
        "output_fields": ["test_type", "statistic", "p_value", "significant"],
        "example": "stats-cli homogeneity levene -g '[10.2,10.5]' -g '[11.3,11.5]'"
    },
    "multiple-comparison": {
        "description": "Multiple comparison: tukey, bonferroni, scheffe",
        "category": "hypothesis",
        "input": ["groups", "test_type", "alpha"],
        "output_fields": ["test_type", "comparisons", "significant_pairs"],
        "example": "stats-cli multiple-comparison tukey -g '[10.2,10.5]' -g '[11.3,11.5]'"
    },
    "equivalence": {
        "description": "Equivalence tests: tost, one_sample_tost",
        "category": "hypothesis",
        "input": ["x", "y", "mu", "delta", "test_type"],
        "output_fields": ["test_type", "t_statistic", "p_value", "equivalent", "ci_90"],
        "example": "stats-cli equivalence tost -v 10.2 -v 10.5 -v2 10.3 -v2 10.6 --delta 0.5"
    },
    "outlier": {
        "description": "Outlier detection: grubbs, dixon, iqr, zscore",
        "category": "basic",
        "input": ["values", "file", "method", "alpha"],
        "output_fields": ["method", "outliers", "n_outliers", "clean_data"],
        "example": "stats-cli outlier -f data.csv -c weight --method grubbs"
    },
    "trend": {
        "description": "Trend analysis: cusum, ewma, runs",
        "category": "spc",
        "input": ["values", "file", "test_type", "target"],
        "output_fields": ["test_type", "alarm_points", "stable"],
        "example": "stats-cli trend -f data.csv -c weight --test-type cusum --target 10.0"
    },
    "doe": {
        "description": "Design of Experiments: full_factorial, fractional_factorial, response_surface, taguchi",
        "category": "doe",
        "input": ["doe_type", "factors", "responses"],
        "output_fields": ["doe_type", "design_matrix", "main_effects", "anova_table"],
        "example": "stats-cli doe full_factorial -f '{\"name\":\"Temp\",\"levels\":3}' -f '{\"name\":\"Time\",\"levels\":2}'"
    },
    "gage-rr": {
        "description": "MSA/Gage R&R: crossed, nested, attribute, bias, linearity, stability",
        "category": "msa",
        "input": ["analysis_type", "measurements", "parts", "operators", "tolerance"],
        "output_fields": ["analysis_type", "variance_components", "contribution", "study_variation", "ndc", "rating"],
        "example": "stats-cli gage-rr crossed -f msa_data.json --tolerance 10.0"
    },
    "clean": {
        "description": "Data cleaning: drop, impute_mean, impute_median, winsorize, clip",
        "category": "data",
        "input": ["values", "file", "method"],
        "output_fields": ["method", "n_original", "n_clean", "n_removed", "before", "after"],
        "example": "stats-cli clean -f data.csv -c weight --method impute_mean"
    },
    "transform": {
        "description": "Data transformation: log, sqrt, boxcox, johnson, rank, standardize, recip",
        "category": "data",
        "input": ["values", "file", "method"],
        "output_fields": ["method", "before", "after", "values"],
        "example": "stats-cli transform -f data.csv -c weight --method boxcox"
    },
    "report": {
        "description": "Generate comprehensive analysis report",
        "category": "report",
        "input": ["values", "file", "usl", "lsl"],
        "output_fields": ["report_file", "analyses"],
        "example": "stats-cli report -f data.csv -c weight --usl 11.0 --lsl 9.0"
    },
    "run": {
        "description": "Run custom R script",
        "category": "advanced",
        "input": ["script_name", "data"],
        "output_fields": ["depends on script"],
        "example": "stats-cli run custom_script.R -d '{\"values\":[1,2,3]}'"
    },
    "explore": {
        "description": "Explore data file structure: columns, types, missing values, basic stats",
        "category": "data",
        "input": ["file", "sheet", "rows"],
        "output_fields": ["n_rows", "n_columns", "columns", "numeric_columns", "sample_data"],
        "example": "stats-cli explore -f data.xlsx"
    },
    "reliability": {
        "description": "Reliability and survival analysis: weibull, kaplan_meier, distribution, stability",
        "category": "reliability",
        "input": ["times", "status", "values", "analysis_type"],
        "output_fields": ["parameters", "b_lives", "mttf", "shelf_life"],
        "example": "stats-cli reliability weibull -t 100 -t 200 -t 300 -s 1 -s 1 -s 1"
    },
    "multivariate": {
        "description": "Multivariate analysis: PCA, cluster, discriminant, correlation_matrix",
        "category": "multivariate",
        "input": ["file", "columns", "groups", "method", "n_clusters"],
        "output_fields": ["eigenvalues", "loadings", "clusters", "accuracy"],
        "example": "stats-cli multivariate pca -f data.csv -c x1 -c x2 -c x3"
    }
}


@click.command("discover")
@click.argument("command_name", required=False)
@click.option("--json-schema", is_flag=True, help="Output JSON schema format")
@click.option("--category", type=click.Choice(["basic", "spc", "hypothesis", "regression", "doe", "msa", "data", "report", "advanced", "all"]),
              default="all", help="Filter by category")
def discover(command_name, json_schema, category):
    """Discover available commands and their capabilities.

    Without arguments, lists all commands.
    With COMMAND_NAME, shows details for that command.

    Examples:

    \b
    # List all commands
    stats-cli discover

    \b
    # Show details for capability command
    stats-cli discover capability

    \b
    # List only SPC commands
    stats-cli discover --category spc
    """
    if command_name:
        if command_name not in COMMANDS:
            raise click.UsageError(f"Unknown command: {command_name}. Use 'stats-cli discover' to list all commands.")

        cmd = COMMANDS[command_name]
        result = {
            "command": command_name,
            "description": cmd["description"],
            "category": cmd["category"],
            "input_parameters": cmd["input"],
            "output_fields": cmd["output_fields"],
            "example": cmd["example"]
        }

        if json_schema:
            result["json_schema"] = {
                "input": {param: "varies" for param in cmd["input"]},
                "output": {field: "varies" for field in cmd["output_fields"]}
            }
    else:
        # List all commands
        filtered = {}
        for name, cmd in COMMANDS.items():
            if category == "all" or cmd["category"] == category:
                filtered[name] = cmd

        result = {
            "total_commands": len(filtered),
            "commands": {
                name: {
                    "description": cmd["description"],
                    "category": cmd["category"],
                    "example": cmd["example"]
                }
                for name, cmd in filtered.items()
            }
        }

    output(result)
