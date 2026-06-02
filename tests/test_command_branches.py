"""Tests for command branches - covering untested code paths."""

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


class TestGageRrBranches:
    """Test gage-rr command branches."""

    def test_crossed_gage_rr(self, runner):
        """Test crossed Gage R&R."""
        result = runner.invoke(main, [
            'gage-rr', 'crossed',
            '-m', '10.1', '-m', '10.2', '-m', '10.3',
            '-m', '10.0', '-m', '10.1', '-m', '10.2',
            '-m', '10.3', '-m', '10.1', '-m', '10.0',
            '-p', 'P1', '-p', 'P1', '-p', 'P1',
            '-p', 'P2', '-p', 'P2', '-p', 'P2',
            '-p', 'P3', '-p', 'P3', '-p', 'P3',
            '-o', 'O1', '-o', 'O2', '-o', 'O3',
            '-o', 'O1', '-o', 'O2', '-o', 'O3',
            '-o', 'O1', '-o', 'O2', '-o', 'O3',
            '--tolerance', '2.0'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['analysis_type'] == 'crossed_gage_rr'

    def test_stability_study(self, runner):
        """Test stability study."""
        result = runner.invoke(main, [
            'gage-rr', 'stability',
            '-m', '10.1', '-m', '10.2', '-m', '10.3', '-m', '10.4', '-m', '10.5'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['analysis_type'] == 'stability'

    def test_linearity_study(self, runner):
        """Test linearity study."""
        result = runner.invoke(main, [
            'gage-rr', 'linearity',
            '-m', '10.1', '-m', '10.2', '-m', '10.3', '-m', '10.4', '-m', '10.5',
            '--reference-values', '10.0', '--reference-values', '10.1',
            '--reference-values', '10.2', '--reference-values', '10.3',
            '--reference-values', '10.4'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['analysis_type'] == 'linearity'


class TestReliabilityBranches:
    """Test reliability command branches."""

    def test_stability_analysis(self, runner):
        """Test stability analysis (shelf life)."""
        result = runner.invoke(main, [
            'reliability', 'stability',
            '-t', '0', '-t', '3', '-t', '6', '-t', '9', '-t', '12',
            '-v', '100', '-v', '99', '-v', '98', '-v', '97', '-v', '96',
            '--lsl', '90'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['analysis_type'] == 'stability'
        assert 'shelf_life' in data

    def test_distribution_fitting(self, runner):
        """Test distribution fitting."""
        result = runner.invoke(main, [
            'reliability', 'distribution',
            '-t', '100', '-t', '200', '-t', '300', '-t', '150', '-t', '250',
            '-s', '1', '-s', '1', '-s', '1', '-s', '1', '-s', '1'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['analysis_type'] == 'distribution'
        assert 'best_distribution' in data


class TestPowerBranches:
    """Test power command branches."""

    def test_anova_power(self, runner):
        """Test ANOVA power analysis."""
        result = runner.invoke(main, [
            'power', 'anova', '--n-groups', '3', '--effect-size', '0.25', '--n', '20'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'power' in data

    def test_anova_sample_size(self, runner):
        """Test ANOVA sample size calculation."""
        result = runner.invoke(main, [
            'power', 'anova', '--n-groups', '3', '--effect-size', '0.25', '--power', '0.80'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'n_per_group' in data

    def test_proportion_sample_size(self, runner):
        """Test proportion sample size calculation."""
        result = runner.invoke(main, [
            'power', 'proportion', '--p0', '0.5', '--p1', '0.6'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'n' in data

    def test_effect_size_cohens_d(self, runner):
        """Test Cohen's d calculation."""
        result = runner.invoke(main, [
            'power', 'effect_size', '--metric', 'cohens_d',
            '--m1', '10', '--m2', '12', '--sd1', '2', '--sd2', '2.5',
            '--n1', '30', '--n2', '30'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'value' in data
        assert 'magnitude' in data


class TestNonparametricBranches:
    """Test nonparametric command branches."""

    def test_kruskal_wallis(self, runner):
        """Test Kruskal-Wallis test."""
        result = runner.invoke(main, [
            'nonparametric', 'kruskal_wallis',
            '-g', '[10.2,10.5,10.1]', '-g', '[11.3,11.5,11.1]', '-g', '[12.1,12.3,12.5]'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['test_type'] == 'kruskal_wallis'

    def test_wilcoxon(self, runner):
        """Test Wilcoxon signed-rank test."""
        result = runner.invoke(main, [
            'nonparametric', 'wilcoxon',
            '--x', '10.2', '--x', '10.5', '--x', '10.1',
            '--y', '10.3', '--y', '10.6', '--y', '10.0'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['test_type'] == 'wilcoxon_signed_rank'

    def test_chi_square_independence(self, runner):
        """Test chi-square independence test."""
        result = runner.invoke(main, [
            'nonparametric', 'chi_square', '--chi-type', 'independence',
            '--observed-matrix', '[[10,20],[30,40]]'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['chi_type'] == 'independence'


class TestTimeseriesBranches:
    """Test timeseries command branches."""

    def test_exp_smoothing(self, runner):
        """Test exponential smoothing."""
        result = runner.invoke(main, [
            'timeseries', 'exp_smoothing',
            '-v', '10', '-v', '12', '-v', '11', '-v', '13', '-v', '14',
            '-v', '12', '-v', '15', '-v', '13', '-v', '16', '-v', '14',
            '--frequency', '4', '--n-forecast', '5'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['analysis_type'] == 'exp_smoothing'
        assert 'forecast' in data


class TestMultivariateBranches:
    """Test multivariate command branches."""

    def test_cluster_hierarchical(self, runner, tmp_path):
        """Test hierarchical clustering."""
        csv_file = tmp_path / "cluster.csv"
        csv_file.write_text("x1,x2\n1,2\n1.5,2.5\n2,3\n8,9\n8.5,9.5\n9,10\n")
        result = runner.invoke(main, [
            'multivariate', 'cluster', '-f', str(csv_file),
            '--method', 'hierarchical', '--n-clusters', '2'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['method'] == 'hierarchical'


class TestEquivalenceBranches:
    """Test equivalence command branches."""

    def test_one_sample_tost(self, runner):
        """Test one-sample TOST."""
        result = runner.invoke(main, [
            'equivalence', 'one_sample_tost',
            '--x', '10.2', '--x', '10.5', '--x', '10.1', '--x', '10.3', '--x', '10.4',
            '--mu', '10.0', '--delta', '0.5'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['test_type'] == 'one_sample_tost'


class TestExploreBranches:
    """Test explore command branches."""

    def test_explore_json(self, runner, tmp_path):
        """Test explore with JSON file."""
        json_file = tmp_path / "test.json"
        json_file.write_text('{"values": [1, 2, 3, 4, 5]}')
        result = runner.invoke(main, ['explore', '-f', str(json_file)])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'format' in data

    def test_explore_text(self, runner, tmp_path):
        """Test explore with text file."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("10.2\n10.5\n10.1\n10.3\n10.4\n")
        result = runner.invoke(main, ['explore', '-f', str(txt_file)])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'format' in data
        assert data['format'] == 'text'
