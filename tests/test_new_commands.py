"""Tests for newly added commands."""

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


class TestNonparametricCommand:
    """Tests for nonparametric command."""

    def test_mann_whitney(self, runner):
        """Test Mann-Whitney U test."""
        result = runner.invoke(main, [
            'nonparametric', 'mann_whitney',
            '--x', '10.2', '--x', '10.5', '--x', '10.1',
            '--y', '11.3', '--y', '11.5', '--y', '11.1'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['test_type'] == 'mann_whitney'
        assert 'p_value' in data

    def test_chi_square_goodness_of_fit(self, runner):
        """Test chi-square goodness of fit."""
        result = runner.invoke(main, [
            'nonparametric', 'chi_square',
            '--observed', '50', '--observed', '30', '--observed', '20'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['test_type'] == 'chi_square'
        assert data['chi_type'] == 'goodness_of_fit'


class TestHomogeneityCommand:
    """Tests for homogeneity command."""

    def test_levene_test(self, runner):
        """Test Levene's test."""
        result = runner.invoke(main, [
            'homogeneity', 'levene',
            '-g', '[10.2,10.5,10.1]', '-g', '[11.3,11.5,11.1]'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'test_type' in data
        assert 'p_value' in data


class TestMultipleComparisonCommand:
    """Tests for multiple-comparison command."""

    def test_tukey_test(self, runner):
        """Test Tukey HSD."""
        result = runner.invoke(main, [
            'multiple-comparison', 'tukey',
            '-g', '[10.2,10.5,10.1]', '-g', '[11.3,11.5,11.1]', '-g', '[12.1,12.3,12.5]'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'test_type' in data


class TestEquivalenceCommand:
    """Tests for equivalence command."""

    def test_tost(self, runner):
        """Test TOST equivalence test."""
        result = runner.invoke(main, [
            'equivalence', 'tost',
            '--x', '10.2', '--x', '10.5', '--x', '10.1',
            '--y', '10.3', '--y', '10.6', '--y', '10.0',
            '--delta', '0.5'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['test_type'] == 'tost'


class TestGageRrCommand:
    """Tests for gage-rr command."""

    def test_bias_study(self, runner):
        """Test bias study."""
        result = runner.invoke(main, [
            'gage-rr', 'bias',
            '-m', '10.1', '-m', '10.2', '-m', '10.3', '-m', '10.0', '-m', '10.2',
            '--reference-value', '10.0'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['analysis_type'] == 'bias'
        assert 'bias' in data


class TestCleanCommand:
    """Tests for clean command."""

    def test_drop_method(self, runner):
        """Test clean with drop method."""
        result = runner.invoke(main, [
            'clean', '-v', '10.1', '-v', '10.2', '-v', '10.3', '--method', 'drop'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['method'] == 'drop'

    def test_impute_mean_method(self, runner):
        """Test clean with impute_mean method."""
        result = runner.invoke(main, [
            'clean', '-v', '10.1', '-v', '10.2', '-v', '10.3', '--method', 'impute_mean'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['method'] == 'impute_mean'


class TestTransformCommand:
    """Tests for transform command."""

    def test_standardize(self, runner):
        """Test standardize transformation."""
        result = runner.invoke(main, [
            'transform', '-v', '10.1', '-v', '10.2', '-v', '10.3', '-v', '10.4', '-v', '10.5',
            '--method', 'standardize'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['method'] == 'standardize'

    def test_log(self, runner):
        """Test log transformation."""
        result = runner.invoke(main, [
            'transform', '-v', '10.1', '-v', '10.2', '-v', '10.3', '--method', 'log'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['method'] == 'log'


class TestDiscoverCommand:
    """Tests for discover command."""

    def test_list_all_commands(self, runner):
        """Test listing all commands."""
        result = runner.invoke(main, ['discover'])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'total_commands' in data
        assert data['total_commands'] > 0

    def test_show_command_details(self, runner):
        """Test showing command details."""
        result = runner.invoke(main, ['discover', 'capability'])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'command' in data
        assert data['command'] == 'capability'


class TestExploreCommand:
    """Tests for explore command."""

    def test_explore_csv(self, runner, tmp_path):
        """Test explore with CSV file."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("x,y\n1,2\n3,4\n5,6\n")
        result = runner.invoke(main, ['explore', '-f', str(csv_file)])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'n_rows' in data
        assert data['n_rows'] == 3


class TestReliabilityCommand:
    """Tests for reliability command."""

    def test_weibull_analysis(self, runner):
        """Test Weibull analysis."""
        result = runner.invoke(main, [
            'reliability', 'weibull',
            '-t', '100', '-t', '200', '-t', '300', '-t', '150', '-t', '250',
            '-s', '1', '-s', '1', '-s', '1', '-s', '1', '-s', '1'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['analysis_type'] == 'weibull'
        assert 'parameters' in data


class TestMultivariateCommand:
    """Tests for multivariate command."""

    def test_cluster_analysis(self, runner, tmp_path):
        """Test cluster analysis."""
        csv_file = tmp_path / "cluster.csv"
        csv_file.write_text("x1,x2\n1,2\n1.5,2.5\n2,3\n8,9\n8.5,9.5\n9,10\n")
        result = runner.invoke(main, [
            'multivariate', 'cluster', '-f', str(csv_file),
            '--method', 'kmeans', '--n-clusters', '2'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['analysis_type'] == 'cluster'
        assert data['n_clusters'] == 2


class TestTimeseriesCommand:
    """Tests for timeseries command."""

    def test_acf_analysis(self, runner):
        """Test ACF analysis."""
        values = [10, 12, 11, 13, 14, 12, 15, 13, 16, 14, 17, 15, 18, 16, 19, 17, 20, 18, 21, 19]
        args = ['timeseries', 'acf']
        for v in values:
            args.extend(['-v', str(v)])
        args.extend(['--max-lag', '5'])

        result = runner.invoke(main, args)
        assert result.exit_code == 0
        data = get_data(result)
        assert data['analysis_type'] == 'acf'
        assert 'acf' in data


class TestPowerCommand:
    """Tests for power command."""

    def test_sample_size_calculation(self, runner):
        """Test sample size calculation."""
        result = runner.invoke(main, [
            'power', 't_test', '--effect-size', '0.5', '--alpha', '0.05', '--power', '0.80'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'n' in data
        assert data['n'] > 0


class TestRunCommand:
    """Tests for run command."""

    def test_run_help(self, runner):
        """Test run command help."""
        result = runner.invoke(main, ['run', '--help'])
        assert result.exit_code == 0
        assert 'Run a custom R script' in result.output
