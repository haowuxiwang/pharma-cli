"""Input validation functions for pharma-cli."""

import click
import sys
from typing import List, Optional, Tuple


def validate_values(values: Tuple[float, ...], min_count: int = 1, name: str = "values") -> List[float]:
    """Validate and convert values tuple to list.

    Args:
        values: Tuple of float values from CLI
        min_count: Minimum number of values required
        name: Name of the parameter for error messages

    Returns:
        List of float values

    Raises:
        click.UsageError: If validation fails
    """
    if not values:
        raise click.UsageError(f"At least {min_count} {name} required")

    if len(values) < min_count:
        raise click.UsageError(f"At least {min_count} {name} required, got {len(values)}")

    # Check for NaN/Inf
    for i, v in enumerate(values):
        if v != v:  # NaN check
            raise click.UsageError(f"NaN value at position {i+1}")
        if abs(v) == float('inf'):
            raise click.UsageError(f"Inf value at position {i+1}")

    return list(values)


def validate_spec_limits(usl: Optional[float], lsl: Optional[float]) -> Tuple[Optional[float], Optional[float]]:
    """Validate specification limits.

    Args:
        usl: Upper specification limit
        lsl: Lower specification limit

    Returns:
        Tuple of (usl, lsl)

    Raises:
        click.UsageError: If validation fails
    """
    if usl is None and lsl is None:
        raise click.UsageError("At least one of --usl or --lsl is required")

    if usl is not None and lsl is not None and usl <= lsl:
        raise click.UsageError(f"USL ({usl}) must be greater than LSL ({lsl})")

    return usl, lsl


def validate_groups(groups: Tuple[str, ...], min_count: int = 2) -> List[List[float]]:
    """Validate and parse group data for ANOVA.

    Args:
        groups: Tuple of JSON array strings
        min_count: Minimum number of groups required

    Returns:
        List of lists of float values

    Raises:
        click.UsageError: If validation fails
    """
    import json

    if len(groups) < min_count:
        raise click.UsageError(f"At least {min_count} groups required, got {len(groups)}")

    result = []
    for i, g in enumerate(groups):
        try:
            parsed = json.loads(g)
            if not isinstance(parsed, list):
                raise click.UsageError(f"Group {i+1} must be a JSON array")
            if len(parsed) < 2:
                raise click.UsageError(f"Group {i+1} must have at least 2 values")
            result.append([float(v) for v in parsed])
        except json.JSONDecodeError as e:
            raise click.UsageError(f"Invalid JSON in group {i+1}: {e}")

    return result


def validate_xy(x: Tuple[float, ...], y: Tuple[float, ...]) -> Tuple[List[float], List[float]]:
    """Validate x and y data for regression/correlation.

    Args:
        x: Tuple of x values
        y: Tuple of y values

    Returns:
        Tuple of (x_list, y_list)

    Raises:
        click.UsageError: If validation fails
    """
    if not x or not y:
        raise click.UsageError("Both --x and --y are required")

    if len(x) != len(y):
        raise click.UsageError(f"--x and --y must have same length, got {len(x)} and {len(y)}")

    if len(x) < 2:
        raise click.UsageError("At least 2 data points required")

    return list(x), list(y)


def validate_alpha(alpha: float) -> float:
    """Validate significance level.

    Args:
        alpha: Significance level

    Returns:
        Validated alpha value

    Raises:
        click.UsageError: If validation fails
    """
    if alpha <= 0 or alpha >= 1:
        raise click.UsageError(f"Alpha must be between 0 and 1, got {alpha}")

    return alpha


def validate_subgroup_size(size: int) -> int:
    """Validate subgroup size for control charts.

    Args:
        size: Subgroup size

    Returns:
        Validated size

    Raises:
        click.UsageError: If validation fails
    """
    if size < 2:
        raise click.UsageError(f"Subgroup size must be at least 2, got {size}")

    return size
