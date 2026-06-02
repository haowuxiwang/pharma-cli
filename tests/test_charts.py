"""Tests for cli/charts.py - Plotly chart generation."""

import pytest
from cli.charts import (
    create_control_chart,
    create_histogram,
    create_qq_plot,
    create_capability_chart,
    create_scatter_plot,
    create_box_plot,
    create_scatter_matrix,
    create_heatmap,
    create_pareto_chart,
    create_diagnostic_plots,
)


class TestCreateControlChart:
    """Test create_control_chart function."""

    def test_basic_control_chart(self):
        """Test basic control chart generation."""
        data = {
            'chart_type': 'imr',
            'chart': {
                'points': [10.2, 10.5, 10.1, 10.3, 10.4],
                'center': 10.3,
                'ucl': 10.8,
                'lcl': 9.8,
                'out_of_control_points': []
            }
        }
        result = create_control_chart(data)
        assert isinstance(result, str)
        assert '<html>' in result or 'plotly' in result.lower()

    def test_control_chart_with_out_of_control(self):
        """Test control chart with out-of-control points."""
        data = {
            'chart_type': 'imr',
            'chart': {
                'points': [10.2, 10.5, 10.1, 10.3, 10.4],
                'center': 10.3,
                'ucl': 10.8,
                'lcl': 9.8,
                'out_of_control_points': [2, 4]
            }
        }
        result = create_control_chart(data)
        assert isinstance(result, str)

    def test_control_chart_with_list_ooc(self):
        """Test control chart with list of out-of-control points."""
        data = {
            'chart_type': 'xbar',
            'chart': {
                'points': [10.2, 10.5, 10.1],
                'center': 10.3,
                'ucl': 10.8,
                'lcl': 9.8,
                'out_of_control_points': [1]
            }
        }
        result = create_control_chart(data)
        assert isinstance(result, str)


class TestCreateHistogram:
    """Test create_histogram function."""

    def test_basic_histogram(self):
        """Test basic histogram generation."""
        data = {
            'histogram': {
                'x': [10.1, 10.2, 10.3, 10.4, 10.5],
                'counts': [5, 10, 15, 10, 5]
            }
        }
        result = create_histogram(data)
        assert isinstance(result, str)

    def test_histogram_with_normal_curve(self):
        """Test histogram with normal curve overlay."""
        data = {
            'histogram': {
                'x': [10.1, 10.2, 10.3, 10.4, 10.5],
                'counts': [5, 10, 15, 10, 5]
            },
            'normal_curve': {
                'x': [10.0, 10.1, 10.2, 10.3, 10.4, 10.5, 10.6],
                'y': [0.1, 0.3, 0.6, 0.8, 0.6, 0.3, 0.1]
            }
        }
        result = create_histogram(data, title="Test Histogram")
        assert isinstance(result, str)


class TestCreateQqPlot:
    """Test create_qq_plot function."""

    def test_basic_qq_plot(self):
        """Test basic Q-Q plot generation."""
        data = {
            'qq_plot': {
                'theoretical': [-1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5],
                'sample': [10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7]
            }
        }
        result = create_qq_plot(data)
        assert isinstance(result, str)


class TestCreateCapabilityChart:
    """Test create_capability_chart function."""

    def test_basic_capability_chart(self):
        """Test basic capability chart generation."""
        data = {
            'histogram': {
                'x': [10.1, 10.2, 10.3, 10.4, 10.5],
                'counts': [5, 10, 15, 10, 5]
            },
            'usl': 11.0,
            'lsl': 9.0,
            'target': 10.0,
            'mean': 10.3,
            'cpk': 1.5,
            'rating': 'Good'
        }
        result = create_capability_chart(data)
        assert isinstance(result, str)

    def test_capability_chart_with_only_usl(self):
        """Test capability chart with only USL."""
        data = {
            'histogram': {
                'x': [10.1, 10.2, 10.3],
                'counts': [5, 10, 5]
            },
            'usl': 11.0,
            'mean': 10.3,
            'cpk': 1.2,
            'rating': 'Acceptable'
        }
        result = create_capability_chart(data)
        assert isinstance(result, str)


class TestCreateScatterPlot:
    """Test create_scatter_plot function."""

    def test_basic_scatter_plot(self):
        """Test basic scatter plot generation."""
        result = create_scatter_plot(
            x=[1, 2, 3, 4, 5],
            y=[2, 4, 6, 8, 10]
        )
        assert isinstance(result, str)

    def test_scatter_plot_with_regression_line(self):
        """Test scatter plot with regression line."""
        result = create_scatter_plot(
            x=[1, 2, 3, 4, 5],
            y=[2, 4, 6, 8, 10],
            regression_line=True,
            title="Test Scatter"
        )
        assert isinstance(result, str)


class TestCreateBoxPlot:
    """Test create_box_plot function."""

    def test_single_group_box_plot(self):
        """Test box plot with single group."""
        result = create_box_plot(data=[10.1, 10.2, 10.3, 10.4, 10.5])
        assert isinstance(result, str)

    def test_multiple_groups_box_plot(self):
        """Test box plot with multiple groups."""
        result = create_box_plot(
            data=[[10.1, 10.2, 10.3], [11.1, 11.2, 11.3]],
            groups=["Group A", "Group B"]
        )
        assert isinstance(result, str)


class TestCreateHeatmap:
    """Test create_heatmap function."""

    def test_basic_heatmap(self):
        """Test basic heatmap generation."""
        result = create_heatmap(
            data=[[1, 2, 3], [4, 5, 6], [7, 8, 9]],
            x_labels=["A", "B", "C"],
            y_labels=["X", "Y", "Z"]
        )
        assert isinstance(result, str)


class TestCreateParetoChart:
    """Test create_pareto_chart function."""

    def test_basic_pareto_chart(self):
        """Test basic Pareto chart generation."""
        result = create_pareto_chart(
            categories=["A", "B", "C", "D"],
            values=[30, 20, 15, 10]
        )
        assert isinstance(result, str)


class TestCreateDiagnosticPlots:
    """Test create_diagnostic_plots function."""

    def test_basic_diagnostic_plots(self):
        """Test basic diagnostic plots generation."""
        data = {
            'residuals': {'mean': 0, 'std': 1},
            'fitted_values': [10.1, 10.2, 10.3, 10.4, 10.5],
            'qq_plot': {
                'theoretical': [-1.5, -1.0, -0.5, 0.0, 0.5],
                'sample': [10.1, 10.2, 10.3, 10.4, 10.5]
            }
        }
        result = create_diagnostic_plots(data)
        assert isinstance(result, dict)
