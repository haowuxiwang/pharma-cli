"""Data cleaning and validation layer for handling real-world dirty data.

This module provides a unified data cleaning pipeline that all data sources
(CSV, Excel, JSON, TXT, stdin) pass through before reaching R scripts.
"""

import math
import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class CleaningReport:
    """Track what was cleaned during data processing."""

    def __init__(self):
        self.original_count: int = 0
        self.cleaned_count: int = 0
        self.removed_nan: int = 0
        self.removed_inf: int = 0
        self.removed_non_numeric: int = 0
        self.warnings: List[str] = []

    @property
    def removed_total(self) -> int:
        return self.original_count - self.cleaned_count

    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_count": self.original_count,
            "cleaned_count": self.cleaned_count,
            "removed_total": self.removed_total,
            "removed_nan": self.removed_nan,
            "removed_inf": self.removed_inf,
            "removed_non_numeric": self.removed_non_numeric,
            "warnings": self.warnings,
        }

    def has_changes(self) -> bool:
        return self.removed_total > 0 or len(self.warnings) > 0


def clean_values(values: List[Any], min_count: int = 1) -> Tuple[List[float], CleaningReport]:
    """Clean a list of values, removing NaN, Inf, and non-numeric entries.

    Args:
        values: Raw values list (may contain None, NaN, Inf, strings, etc.)
        min_count: Minimum number of clean values required

    Returns:
        Tuple of (clean_values, cleaning_report)

    Raises:
        ValueError: If fewer than min_count clean values remain after cleaning
    """
    report = CleaningReport()
    report.original_count = len(values)
    clean = []

    for i, v in enumerate(values):
        # Skip None
        if v is None:
            report.removed_nan += 1
            continue

        # Try to convert to float
        try:
            fv = float(v)
        except (ValueError, TypeError):
            report.removed_non_numeric += 1
            report.warnings.append(f"Skipped non-numeric value at position {i+1}: {repr(v)}")
            continue

        # Skip NaN
        if math.isnan(fv):
            report.removed_nan += 1
            continue

        # Skip Inf
        if math.isinf(fv):
            report.removed_inf += 1
            report.warnings.append(f"Skipped infinite value at position {i+1}")
            continue

        clean.append(fv)

    report.cleaned_count = len(clean)

    if len(clean) < min_count:
        raise ValueError(
            f"Need at least {min_count} valid numeric values, "
            f"got {len(clean)} after cleaning "
            f"(removed {report.removed_nan} NaN, "
            f"{report.removed_inf} Inf, "
            f"{report.removed_non_numeric} non-numeric)"
        )

    return clean, report


def detect_encoding(file_path: str) -> str:
    """Detect file encoding.

    Tries UTF-8 first, then falls back to common encodings.
    Returns encoding name suitable for open().
    """
    encodings_to_try = ["utf-8-sig", "utf-8", "gbk", "gb2312", "gb18030", "latin-1"]

    for enc in encodings_to_try:
        try:
            with open(file_path, "r", encoding=enc) as f:
                f.read(4096)  # Read a chunk to test
            return enc
        except (UnicodeDecodeError, UnicodeError):
            continue

    return "utf-8"  # Ultimate fallback


def detect_delimiter(file_path: str, encoding: str = "utf-8") -> str:
    """Detect CSV delimiter.

    Reads the first few lines and uses csv.Sniffer to detect.
    Falls back to comma if detection fails.
    """
    import csv

    try:
        with open(file_path, "r", encoding=encoding, newline="") as f:
            sample = f.read(8192)
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        return dialect.delimiter
    except (csv.Error, Exception):
        return ","
