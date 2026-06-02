"""Commands package for stats-cli."""
from .descriptive import descriptive
from .normality import normality
from .capability import capability
from .control_chart import control_chart
from .ttest import ttest
from .anova import anova
from .regression import regression
from .correlation import correlation
from .nonparametric import nonparametric
from .homogeneity import homogeneity
from .multiple_comparison import multiple_comparison
from .equivalence import equivalence
from .outlier import outlier
from .trend import trend
from .doe import doe
from .run import run
from .report import report
from .gage_rr import gage_rr
from .clean import clean
from .transform import transform
from .discover import discover
from .explore import explore
from .reliability import reliability
from .multivariate import multivariate
from .timeseries import timeseries
from .power import power

__all__ = [
    "descriptive",
    "normality",
    "capability",
    "control_chart",
    "ttest",
    "anova",
    "regression",
    "correlation",
    "nonparametric",
    "homogeneity",
    "multiple_comparison",
    "equivalence",
    "outlier",
    "trend",
    "doe",
    "run",
    "report",
    "gage_rr",
    "clean",
    "transform",
    "discover",
    "explore",
    "reliability",
    "multivariate",
    "timeseries",
    "power",
]
