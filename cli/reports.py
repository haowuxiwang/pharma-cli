"""Report generation module using Jinja2."""

from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


class ReportGenerator:
    """Generate HTML reports from statistical analysis results."""

    def __init__(self):
        """Initialize the report generator with templates."""
        template_dir = Path(__file__).parent / "templates"
        self.env = Environment(loader=FileSystemLoader(template_dir))

    def generate_descriptive_report(self, data: Dict[str, Any],
                                   chart: Optional[str] = None) -> str:
        """Generate descriptive statistics report.

        Args:
            data: Descriptive statistics data
            chart: Optional HTML chart string

        Returns:
            HTML report string
        """
        template = self.env.get_template("descriptive.html")
        return template.render(
            data=data,
            chart=chart,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

    def generate_normality_report(self, data: Dict[str, Any],
                                 charts: Optional[Dict[str, str]] = None) -> str:
        """Generate normality test report.

        Args:
            data: Normality test data
            charts: Optional dictionary of HTML chart strings

        Returns:
            HTML report string
        """
        template = self.env.get_template("normality.html")
        return template.render(
            data=data,
            charts=charts or {},
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

    def generate_capability_report(self, data: Dict[str, Any],
                                  chart: Optional[str] = None) -> str:
        """Generate process capability report.

        Args:
            data: Process capability data
            chart: Optional HTML chart string

        Returns:
            HTML report string
        """
        template = self.env.get_template("capability.html")
        return template.render(
            data=data,
            chart=chart,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

    def generate_control_chart_report(self, data: Dict[str, Any],
                                     chart: Optional[str] = None) -> str:
        """Generate control chart report.

        Args:
            data: Control chart data
            chart: Optional HTML chart string

        Returns:
            HTML report string
        """
        template = self.env.get_template("control_chart.html")
        return template.render(
            data=data,
            chart=chart,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

    def generate_regression_report(self, data: Dict[str, Any],
                                  charts: Optional[Dict[str, str]] = None) -> str:
        """Generate regression analysis report.

        Args:
            data: Regression analysis data
            charts: Optional dictionary of HTML chart strings

        Returns:
            HTML report string
        """
        template = self.env.get_template("regression.html")
        return template.render(
            data=data,
            charts=charts or {},
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

    def generate_comprehensive_report(self, analyses: Dict[str, Any],
                                     charts: Optional[Dict[str, str]] = None) -> str:
        """Generate comprehensive analysis report.

        Args:
            analyses: Dictionary of analysis results
            charts: Optional dictionary of HTML chart strings

        Returns:
            HTML report string
        """
        template = self.env.get_template("comprehensive.html")
        return template.render(
            analyses=analyses,
            charts=charts or {},
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
