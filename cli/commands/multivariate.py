"""Multivariate analysis command."""
import json
import click

from cli.r_engine import run_r_file
from cli.commands.utils import output


@click.command()
@click.argument("analysis_type", type=click.Choice([
    "pca", "cluster", "discriminant", "correlation_matrix"
]))
@click.option("--file", "-f", "data_file", type=click.Path(exists=True), help="CSV/Excel file with data")
@click.option("--columns", "-c", multiple=True, help="Column names to include (default: all numeric)")
@click.option("--groups", "-g", default=None, help="Group column name (for discriminant)")
@click.option("--method", type=click.Choice(["hierarchical", "kmeans"]), default="hierarchical",
              help="Clustering method")
@click.option("--n-clusters", type=int, default=3, help="Number of clusters")
@click.option("--cor-method", type=click.Choice(["pearson", "spearman", "kendall"]), default="pearson",
              help="Correlation method")
@click.pass_context
def multivariate(ctx, analysis_type, data_file, columns, groups, method, n_clusters, cor_method):
    """Multivariate analysis: PCA, clustering, discriminant, correlation matrix.

    ANALYSIS_TYPE: pca, cluster, discriminant, correlation_matrix

    Examples:

    \b
    # PCA
    stats-cli multivariate pca -f data.csv -c "x1" -c "x2" -c "x3"

    \b
    # Hierarchical clustering
    stats-cli multivariate cluster -f data.xlsx --method hierarchical --n-clusters 3

    \b
    # Discriminant analysis
    stats-cli multivariate discriminant -f data.csv -c "x1" -c "x2" -g "group"

    \b
    # Correlation matrix
    stats-cli multivariate correlation_matrix -f data.csv
    """
    if not data_file:
        raise click.UsageError("--file is required for multivariate analysis")

    # Load data
    data_matrix, group_data = _load_multivariate_data(data_file, columns, groups)

    # Build request
    request = {
        "analysis_type": analysis_type,
        "data": data_matrix,
    }

    if analysis_type == "cluster":
        request["method"] = method
        request["n_clusters"] = n_clusters
    elif analysis_type == "discriminant":
        if group_data is None:
            raise click.UsageError("--groups column required for discriminant analysis")
        request["groups"] = group_data
    elif analysis_type == "correlation_matrix":
        request["method"] = cor_method

    result = run_r_file("multivariate.R", request)
    output(result)


def _load_multivariate_data(file_path, columns, group_column):
    """Load multivariate data from file.

    Returns:
        tuple: (data_matrix as list of lists, group_data as list or None)
    """
    from pathlib import Path
    import pandas as pd
    import numpy as np

    path = Path(file_path)
    suffix = path.suffix.lower()

    # Load DataFrame
    if suffix in [".xlsx", ".xls"]:
        df = pd.read_excel(path)
    elif suffix == ".csv":
        from cli.data_cleaner import detect_encoding, detect_delimiter
        encoding = detect_encoding(str(path))
        delimiter = detect_delimiter(str(path), encoding)
        df = pd.read_csv(path, encoding=encoding, sep=delimiter)
    else:
        raise click.UsageError(f"Unsupported file format: {suffix}")

    # Select columns
    if columns:
        # Use specified columns
        missing = [c for c in columns if c not in df.columns]
        if missing:
            raise click.UsageError(f"Columns not found: {missing}. Available: {list(df.columns)}")
        numeric_cols = [c for c in columns if pd.api.types.is_numeric_dtype(df[c])]
        non_numeric = [c for c in columns if not pd.api.types.is_numeric_dtype(df[c])]
        if non_numeric:
            raise click.UsageError(f"Non-numeric columns: {non_numeric}")
    else:
        # Auto-detect numeric columns (excluding group column)
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if group_column and group_column in numeric_cols:
            numeric_cols.remove(group_column)

    if len(numeric_cols) < 2:
        raise click.UsageError(f"Need at least 2 numeric columns. Found: {numeric_cols}")

    # Extract data matrix
    data_matrix = df[numeric_cols].dropna().values.tolist()

    # Extract group data if specified
    group_data = None
    if group_column:
        if group_column not in df.columns:
            raise click.UsageError(f"Group column '{group_column}' not found")
        group_data = df[group_column].dropna().astype(str).tolist()
        # Align with data_matrix (drop rows where group is NaN)
        mask = df[numeric_cols + [group_column]].notna().all(axis=1)
        data_matrix = df.loc[mask, numeric_cols].values.tolist()
        group_data = df.loc[mask, group_column].astype(str).tolist()

    return data_matrix, group_data
