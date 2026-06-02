"""Tests for cli/reports.py - Report generation."""

import pytest
from cli.reports import ReportGenerator


@pytest.fixture
def generator():
    """Create a ReportGenerator instance."""
    return ReportGenerator()


class TestReportGenerator:
    """Test ReportGenerator class."""

    def test_init(self, generator):
        """Test ReportGenerator initialization."""
        assert generator is not None
        assert hasattr(generator, 'env')

    def test_generate_descriptive_report(self, generator):
        """Test descriptive report generation."""
        data = {
            'n': 5,
            'mean': 10.3,
            'median': 10.3,
            'std': 0.1581,
            'rsd_percent': 1.54,
            'min': 10.1,
            'max': 10.5,
            'range': 0.4,
            'q1': 10.2,
            'q3': 10.4,
            'iqr': 0.2,
            'ci_95_lower': 10.11,
            'ci_95_upper': 10.49,
            'skewness': 0.0,
            'kurtosis': -1.2
        }
        result = generator.generate_descriptive_report(data)
        assert isinstance(result, str)
        assert '<html>' in result.lower()

    def test_generate_descriptive_report_with_chart(self, generator):
        """Test descriptive report with chart."""
        data = {
            'n': 5,
            'mean': 10.3,
            'median': 10.3,
            'std': 0.1581,
            'rsd_percent': 1.54,
            'min': 10.1,
            'max': 10.5,
            'range': 0.4,
            'q1': 10.2,
            'q3': 10.4,
            'iqr': 0.2,
            'ci_95_lower': 10.11,
            'ci_95_upper': 10.49,
            'skewness': 0.0,
            'kurtosis': -1.2
        }
        chart = '<div>Test Chart</div>'
        result = generator.generate_descriptive_report(data, chart)
        assert isinstance(result, str)

    def test_generate_normality_report(self, generator):
        """Test normality report generation."""
        data = {
            'shapiro_wilk': {'statistic': 0.95, 'p_value': 0.5, 'is_normal': True},
            'anderson_darling': {'statistic': 0.3, 'p_value': 0.6},
            'lilliefors': {'statistic': 0.05, 'p_value': 0.7},
            'is_normal': True,
            'interpretation': 'Data is normally distributed'
        }
        result = generator.generate_normality_report(data)
        assert isinstance(result, str)

    def test_generate_capability_report(self, generator):
        """Test capability report generation."""
        data = {
            'mean': 10.3,
            'std_within': 0.15,
            'std_overall': 0.16,
            'usl': 11.0,
            'lsl': 9.0,
            'target': 10.0,
            'cp': 2.22,
            'cpk': 1.87,
            'pp': 2.08,
            'ppk': 1.75,
            'rating': 'Excellent',
            'rating_desc': 'Process is highly capable',
            'n': 100
        }
        result = generator.generate_capability_report(data)
        assert isinstance(result, str)

    def test_generate_capability_report_with_chart(self, generator):
        """Test capability report with chart."""
        data = {
            'mean': 10.3,
            'std_within': 0.15,
            'std_overall': 0.16,
            'usl': 11.0,
            'lsl': 9.0,
            'target': 10.0,
            'cp': 2.22,
            'cpk': 1.87,
            'pp': 2.08,
            'ppk': 1.75,
            'rating': 'Excellent',
            'rating_desc': 'Process is highly capable',
            'n': 100
        }
        chart = '<div>Test Chart</div>'
        result = generator.generate_capability_report(data, chart)
        assert isinstance(result, str)

    def test_generate_comprehensive_report(self, generator):
        """Test comprehensive report generation."""
        analyses = {
            'descriptive': {
                'n': 100,
                'mean': 10.3,
                'median': 10.3,
                'std': 0.15,
                'rsd_percent': 1.46,
                'min': 10.0,
                'max': 10.6,
                'range': 0.6,
                'q1': 10.2,
                'q3': 10.4,
                'iqr': 0.2,
                'ci_95_lower': 10.1,
                'ci_95_upper': 10.5,
                'skewness': 0.0,
                'kurtosis': -0.5
            },
            'normality': {
                'is_normal': True,
                'shapiro_wilk': {'statistic': 0.95, 'p_value': 0.5, 'is_normal': True},
                'anderson_darling': {'statistic': 0.3, 'p_value': 0.6},
                'lilliefors': {'statistic': 0.05, 'p_value': 0.7}
            },
            'capability': {
                'mean': 10.3,
                'std_within': 0.15,
                'std_overall': 0.16,
                'usl': 11.0,
                'lsl': 9.0,
                'target': 10.0,
                'cp': 2.22,
                'cpk': 1.87,
                'pp': 2.08,
                'ppk': 1.75,
                'rating': 'Excellent',
                'n': 100
            },
            'control_chart': {
                'chart_type': 'imr',
                'chart': {
                    'points': [10.2, 10.5, 10.1, 10.3, 10.4],
                    'center': 10.3,
                    'ucl': 10.8,
                    'lcl': 9.8,
                    'out_of_control_points': []
                },
                'summary': {'stable': True}
            }
        }
        result = generator.generate_comprehensive_report(analyses)
        assert isinstance(result, str)
