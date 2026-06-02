"""Integration tests for pharma-cli."""

import pytest
import json
from click.testing import CliRunner
from cli.main import main


@pytest.fixture
def runner():
    """Create a Click test runner."""
    return CliRunner()


def get_data(result):
    """Extract data from wrapped JSON output."""
    output = json.loads(result.output)
    if "data" in output:
        return output["data"]
    return output


class TestFullWorkflow:
    """Test complete workflows."""

    def test_data_quality_workflow(self, runner):
        """Test data quality check workflow."""
        # Step 1: Descriptive statistics
        result = runner.invoke(main, ['descriptive', '-v', '10.2', '-v', '10.5', '-v', '10.1', '-v', '10.3', '-v', '10.4'])
        assert result.exit_code == 0
        desc_data = get_data(result)
        assert desc_data['n'] == 5

        # Step 2: Normality test
        result = runner.invoke(main, ['normality', '-v', '10.2', '-v', '10.5', '-v', '10.1', '-v', '10.3', '-v', '10.4'])
        assert result.exit_code == 0
        norm_data = get_data(result)
        assert 'is_normal' in norm_data

        # Step 3: Outlier detection (use IQR method which is more robust)
        result = runner.invoke(main, ['outlier', '-v', '10.2', '-v', '10.5', '-v', '10.1', '-v', '10.3', '-v', '10.4', '--method', 'iqr'])
        assert result.exit_code == 0
        outlier_data = get_data(result)
        assert 'outliers' in outlier_data

    def test_process_capability_workflow(self, runner):
        """Test process capability study workflow."""
        # Step 1: Descriptive statistics
        result = runner.invoke(main, ['descriptive', '-v', '10.2', '-v', '10.5', '-v', '10.1', '-v', '10.3', '-v', '10.4'])
        assert result.exit_code == 0
        desc_data = get_data(result)
        assert 'mean' in desc_data
        assert 'std' in desc_data

        # Step 2: Normality check
        result = runner.invoke(main, ['normality', '-v', '10.2', '-v', '10.5', '-v', '10.1', '-v', '10.3', '-v', '10.4'])
        assert result.exit_code == 0
        norm_data = get_data(result)
        assert 'is_normal' in norm_data

        # Step 3: Capability analysis
        result = runner.invoke(main, ['capability', '-v', '10.2', '-v', '10.5', '-v', '10.1', '-v', '10.3', '-v', '10.4', '--usl', '11.0', '--lsl', '9.0'])
        assert result.exit_code == 0
        cap_data = get_data(result)
        assert 'cp' in cap_data
        assert 'cpk' in cap_data
        assert 'rating' in cap_data

    def test_spc_monitoring_workflow(self, runner):
        """Test SPC monitoring workflow."""
        # Step 1: I-MR chart
        result = runner.invoke(main, ['control-chart', 'imr', '-v', '10.2', '-v', '10.5', '-v', '10.1', '-v', '10.3', '-v', '10.4', '-v', '10.6', '-v', '10.3', '-v', '10.5', '-v', '10.2', '-v', '10.4'])
        assert result.exit_code == 0
        imr_data = get_data(result)
        assert imr_data['chart_type'] == 'imr'
        assert 'chart' in imr_data
        assert 'summary' in imr_data

        # Step 2: Check stability
        assert imr_data['summary']['stable'] is True

    def test_hypothesis_testing_workflow(self, runner):
        """Test hypothesis testing workflow."""
        # Step 1: One-sample t-test
        result = runner.invoke(main, ['ttest', 'one_sample', '-v', '10.2', '-v', '10.5', '-v', '10.1', '-v', '10.3', '-v', '10.4', '--mu', '10.0'])
        assert result.exit_code == 0
        ttest_data = get_data(result)
        assert 't_statistic' in ttest_data
        assert 'p_value' in ttest_data
        assert 'significant' in ttest_data

        # Step 2: Two-sample t-test
        result = runner.invoke(main, ['ttest', 'two_sample', '-v', '10.2', '-v', '10.5', '-v', '10.1', '-v2', '11.3', '-v2', '11.5', '-v2', '11.1'])
        assert result.exit_code == 0
        ttest2_data = get_data(result)
        assert ttest2_data['test_type'] == 'two_sample'

    def test_regression_analysis_workflow(self, runner):
        """Test regression analysis workflow."""
        # Step 1: Linear regression
        result = runner.invoke(main, ['regression', '--x', '1', '--x', '2', '--x', '3', '--x', '4', '--x', '5', '--y', '2.1', '--y', '3.9', '--y', '6.2', '--y', '7.8', '--y', '10.1'])
        assert result.exit_code == 0
        reg_data = get_data(result)
        assert reg_data['regression_type'] == 'linear'
        assert 'r_squared' in reg_data
        assert 'coefficients' in reg_data

        # Step 2: Check R-squared
        assert reg_data['r_squared'] > 0.9

    def test_doe_workflow(self, runner):
        """Test DOE workflow."""
        # Step 1: Create design
        result = runner.invoke(main, ['doe', 'full_factorial', '-f', '{"name":"Temp","levels":3}', '-f', '{"name":"Time","levels":2}'])
        assert result.exit_code == 0
        doe_data = get_data(result)
        assert doe_data['doe_type'] == 'full_factorial'
        assert 'design_matrix' in doe_data


class TestErrorHandling:
    """Test error handling."""

    def test_invalid_data_handling(self, runner):
        """Test handling of invalid data."""
        # Test with empty data
        result = runner.invoke(main, ['descriptive'])
        assert result.exit_code != 0
        assert 'valid numeric values' in result.output

    def test_invalid_parameters_handling(self, runner):
        """Test handling of invalid parameters."""
        # Test with invalid alpha
        result = runner.invoke(main, ['outlier', '-v', '10.2', '-v', '10.5', '-v', '10.1', '--alpha', '2.0'])
        assert result.exit_code != 0
        assert 'Alpha must be between 0 and 1' in result.output

    def test_file_not_found_handling(self, runner):
        """Test handling of file not found."""
        result = runner.invoke(main, ['descriptive', '-f', '/nonexistent/file.csv'])
        assert result.exit_code != 0


class TestChartGeneration:
    """Test chart generation integration."""

    def test_control_chart_with_plot(self, runner):
        """Test control chart with plot generation."""
        result = runner.invoke(main, ['--plot', 'control-chart', 'imr', '-v', '10.2', '-v', '10.5', '-v', '10.1', '-v', '10.3', '-v', '10.4'])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'plot' in data
        assert len(data['plot']) > 0

    def test_normality_with_plot(self, runner):
        """Test normality with plot generation."""
        result = runner.invoke(main, ['--plot', 'normality', '-v', '10.2', '-v', '10.5', '-v', '10.1', '-v', '10.3', '-v', '10.4'])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'plot' in data
        assert len(data['plot']) > 0

    def test_capability_with_plot(self, runner):
        """Test capability with plot generation."""
        result = runner.invoke(main, ['--plot', 'capability', '-v', '10.2', '-v', '10.5', '-v', '10.1', '-v', '10.3', '-v', '10.4', '--usl', '11.0', '--lsl', '9.0'])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'plot' in data
        assert len(data['plot']) > 0
