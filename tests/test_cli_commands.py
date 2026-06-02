"""Tests for cli/main.py CLI commands."""

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


class TestDescriptiveCommand:
    """Tests for descriptive command."""

    def test_descriptive_with_values(self, runner):
        """Test descriptive with values."""
        result = runner.invoke(main, ['descriptive', '-v', '10.2', '-v', '10.5', '-v', '10.1'])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'n' in data
        assert 'mean' in data
        assert 'std' in data
        assert data['n'] == 3

    def test_descriptive_with_file(self, runner, sample_csv_file):
        """Test descriptive with file."""
        result = runner.invoke(main, ['descriptive', '-f', sample_csv_file, '-c', 'measurement'])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'n' in data
        assert data['n'] == 5

    def test_descriptive_no_data(self, runner):
        """Test descriptive with no data."""
        result = runner.invoke(main, ['descriptive'])
        assert result.exit_code != 0
        assert 'valid numeric values' in result.output


class TestNormalityCommand:
    """Tests for normality command."""

    def test_normality_with_values(self, runner):
        """Test normality with values."""
        result = runner.invoke(main, ['normality', '-v', '10.2', '-v', '10.5', '-v', '10.1', '-v', '10.3', '-v', '10.4'])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'shapiro_wilk' in data
        assert 'is_normal' in data

    def test_normality_with_file(self, runner, sample_csv_file):
        """Test normality with file."""
        result = runner.invoke(main, ['normality', '-f', sample_csv_file, '-c', 'measurement'])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'shapiro_wilk' in data


class TestCapabilityCommand:
    """Tests for capability command."""

    def test_capability_with_values(self, runner):
        """Test capability with values."""
        result = runner.invoke(main, ['capability', '-v', '10.2', '-v', '10.5', '-v', '10.1', '--usl', '11.0', '--lsl', '9.0'])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'cp' in data
        assert 'cpk' in data
        assert 'rating' in data

    def test_capability_with_file(self, runner, sample_csv_file):
        """Test capability with file."""
        result = runner.invoke(main, ['capability', '-f', sample_csv_file, '-c', 'measurement', '--usl', '11.0', '--lsl', '9.0'])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'cp' in data

    def test_capability_no_limits(self, runner):
        """Test capability with no limits."""
        result = runner.invoke(main, ['capability', '-v', '10.2', '-v', '10.5', '-v', '10.1'])
        assert result.exit_code != 0
        assert 'At least one of --usl or --lsl is required' in result.output

    def test_capability_invalid_limits(self, runner):
        """Test capability with invalid limits."""
        result = runner.invoke(main, ['capability', '-v', '10.2', '-v', '10.5', '-v', '10.1', '--usl', '9.0', '--lsl', '11.0'])
        assert result.exit_code != 0
        assert 'must be greater than LSL' in result.output


class TestControlChartCommand:
    """Tests for control-chart command."""

    def test_imr_chart(self, runner):
        """Test I-MR chart."""
        result = runner.invoke(main, ['control-chart', 'imr', '-v', '10.2', '-v', '10.5', '-v', '10.1', '-v', '10.3', '-v', '10.4'])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'chart_type' in data
        assert data['chart_type'] == 'imr'

    def test_xbar_chart(self, runner):
        """Test X-bar chart."""
        result = runner.invoke(main, ['control-chart', 'xbar', '-v', '10.2', '-v', '10.5', '-v', '10.1', '-v', '10.3', '-v', '10.4', '-v', '10.6', '-v', '10.3', '-v', '10.5', '-v', '10.2', '-v', '10.4'])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'chart_type' in data
        assert data['chart_type'] == 'xbar'

    def test_control_chart_with_file(self, runner, sample_csv_file):
        """Test control chart with file."""
        result = runner.invoke(main, ['control-chart', 'imr', '-f', sample_csv_file, '-c', 'measurement'])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'chart_type' in data


class TestTtestCommand:
    """Tests for ttest command."""

    def test_one_sample_ttest(self, runner):
        """Test one-sample t-test."""
        result = runner.invoke(main, ['ttest', 'one_sample', '-v', '10.2', '-v', '10.5', '-v', '10.1', '--mu', '10.0'])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'test_type' in data
        assert data['test_type'] == 'one_sample'

    def test_two_sample_ttest(self, runner):
        """Test two-sample t-test."""
        result = runner.invoke(main, ['ttest', 'two_sample', '-v', '10.2', '-v', '10.5', '-v', '10.1', '-v2', '11.3', '-v2', '11.5', '-v2', '11.1'])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'test_type' in data
        assert data['test_type'] == 'two_sample'

    def test_paired_ttest(self, runner):
        """Test paired t-test."""
        result = runner.invoke(main, ['ttest', 'paired', '-v', '10.2', '-v', '10.5', '-v', '10.1', '-v2', '10.8', '-v2', '10.9', '-v2', '10.7'])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'test_type' in data
        assert data['test_type'] == 'paired'


class TestAnovaCommand:
    """Tests for anova command."""

    def test_one_way_anova(self, runner):
        """Test one-way ANOVA."""
        result = runner.invoke(main, ['anova', 'one_way', '-g', '[10.2,10.5,10.1]', '-g', '[11.3,11.5,11.1]'])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'anova_type' in data
        assert data['anova_type'] == 'one_way'

    def test_anova_insufficient_groups(self, runner):
        """Test ANOVA with insufficient groups."""
        result = runner.invoke(main, ['anova', 'one_way', '-g', '[10.2,10.5,10.1]'])
        assert result.exit_code != 0
        assert 'At least 2 groups required' in result.output


class TestRegressionCommand:
    """Tests for regression command."""

    def test_linear_regression(self, runner):
        """Test linear regression."""
        result = runner.invoke(main, ['regression', '--x', '1', '--x', '2', '--x', '3', '--y', '2', '--y', '4', '--y', '6'])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'regression_type' in data
        assert data['regression_type'] == 'linear'
        assert 'r_squared' in data

    def test_regression_with_file(self, runner, tmp_path):
        """Test regression with file."""
        csv_content = "x,y\n1,2\n2,4\n3,6\n"
        csv_file = tmp_path / "regression.csv"
        csv_file.write_text(csv_content)
        result = runner.invoke(main, ['regression', '-f', str(csv_file)])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'regression_type' in data


class TestCorrelationCommand:
    """Tests for correlation command."""

    def test_pearson_correlation(self, runner):
        """Test Pearson correlation."""
        result = runner.invoke(main, ['correlation', '--x', '1', '--x', '2', '--x', '3', '--y', '2', '--y', '4', '--y', '6'])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'method' in data
        assert data['method'] == 'pearson'
        assert 'correlation' in data

    def test_spearman_correlation(self, runner):
        """Test Spearman correlation."""
        result = runner.invoke(main, ['correlation', '--x', '1', '--x', '2', '--x', '3', '--y', '2', '--y', '4', '--y', '6', '--method', 'spearman'])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['method'] == 'spearman'


class TestOutlierCommand:
    """Tests for outlier command."""

    def test_grubbs_outlier(self, runner):
        """Test Grubbs outlier detection."""
        result = runner.invoke(main, ['outlier', '-v', '10.2', '-v', '10.5', '-v', '10.1', '-v', '15.0', '--method', 'grubbs'])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'method' in data
        assert data['method'] == 'grubbs'
        assert 'outliers' in data

    def test_outlier_invalid_alpha(self, runner):
        """Test outlier with invalid alpha."""
        result = runner.invoke(main, ['outlier', '-v', '10.2', '-v', '10.5', '-v', '10.1', '--alpha', '2.0'])
        assert result.exit_code != 0
        assert 'Alpha must be between 0 and 1' in result.output


class TestTrendCommand:
    """Tests for trend command."""

    def test_cusum_trend(self, runner):
        """Test CUSUM trend analysis."""
        result = runner.invoke(main, ['trend', '-v', '10.2', '-v', '10.5', '-v', '10.1', '-v', '10.3', '-v', '10.4', '--test-type', 'cusum', '--target', '10.3'])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'test_type' in data
        assert data['test_type'] == 'cusum'


class TestDoeCommand:
    """Tests for doe command."""

    def test_full_factorial_doe(self, runner):
        """Test full factorial DOE."""
        result = runner.invoke(main, ['doe', 'full_factorial', '-f', '{"name":"Temp","levels":3}', '-f', '{"name":"Time","levels":2}'])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'doe_type' in data
        assert data['doe_type'] == 'full_factorial'


class TestPlotOption:
    """Tests for --plot option."""

    def test_plot_option_with_control_chart(self, runner):
        """Test --plot option with control chart."""
        result = runner.invoke(main, ['--plot', 'control-chart', 'imr', '-v', '10.2', '-v', '10.5', '-v', '10.1', '-v', '10.3', '-v', '10.4'])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'plot' in data

    def test_plot_option_with_normality(self, runner):
        """Test --plot option with normality."""
        result = runner.invoke(main, ['--plot', 'normality', '-v', '10.2', '-v', '10.5', '-v', '10.1', '-v', '10.3', '-v', '10.4'])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'plot' in data


class TestLoadData:
    """Tests for _load_data function."""

    def test_load_data_from_values(self, runner):
        """Test loading data from values."""
        result = runner.invoke(main, ['descriptive', '-v', '10.2', '-v', '10.5', '-v', '10.1'])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['n'] == 3

    def test_load_data_from_csv(self, runner, sample_csv_file):
        """Test loading data from CSV file."""
        result = runner.invoke(main, ['descriptive', '-f', sample_csv_file, '-c', 'measurement'])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['n'] == 5

    def test_load_data_from_txt(self, runner, sample_txt_file):
        """Test loading data from TXT file."""
        result = runner.invoke(main, ['descriptive', '-f', sample_txt_file])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['n'] == 5

    def test_load_data_from_json(self, runner, sample_json_file):
        """Test loading data from JSON file."""
        result = runner.invoke(main, ['descriptive', '-f', sample_json_file])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['n'] == 5


class TestOutput:
    """Tests for _output function."""

    def test_json_output(self, runner):
        """Test JSON output format."""
        result = runner.invoke(main, ['descriptive', '-v', '10.2', '-v', '10.5', '-v', '10.1'])
        assert result.exit_code == 0
        output = json.loads(result.output)
        assert 'status' in output
        assert 'version' in output
        assert 'timestamp' in output
        assert 'data' in output
        assert output['status'] == 'success'
