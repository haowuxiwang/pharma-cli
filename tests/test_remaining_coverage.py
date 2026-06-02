"""Tests for remaining coverage gaps."""

import pytest
import json
import pandas as pd
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


class TestGageRrExtended:
    """Test gage-rr command additional branches."""

    def test_crossed_with_replicates(self, runner):
        """Test crossed Gage R&R with replicates (r > 1)."""
        result = runner.invoke(main, [
            'gage-rr', 'crossed',
            '-m', '10.1', '-m', '10.2', '-m', '10.3',
            '-m', '10.0', '-m', '10.1', '-m', '10.2',
            '-m', '10.3', '-m', '10.1', '-m', '10.0',
            '-m', '10.2', '-m', '10.3', '-m', '10.1',
            '-m', '10.0', '-m', '10.1', '-m', '10.2',
            '-m', '10.3', '-m', '10.1', '-m', '10.0',
            '-p', 'P1', '-p', 'P1', '-p', 'P1',
            '-p', 'P2', '-p', 'P2', '-p', 'P2',
            '-p', 'P3', '-p', 'P3', '-p', 'P3',
            '-p', 'P1', '-p', 'P1', '-p', 'P1',
            '-p', 'P2', '-p', 'P2', '-p', 'P2',
            '-p', 'P3', '-p', 'P3', '-p', 'P3',
            '-o', 'O1', '-o', 'O2', '-o', 'O3',
            '-o', 'O1', '-o', 'O2', '-o', 'O3',
            '-o', 'O1', '-o', 'O2', '-o', 'O3',
            '-o', 'O1', '-o', 'O2', '-o', 'O3',
            '-o', 'O1', '-o', 'O2', '-o', 'O3',
            '-o', 'O1', '-o', 'O2', '-o', 'O3',
            '--tolerance', '2.0'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['analysis_type'] == 'crossed_gage_rr'
        assert data['has_interaction'] is True

    def test_linearity_with_multiple_points(self, runner):
        """Test linearity study with multiple reference points."""
        result = runner.invoke(main, [
            'gage-rr', 'linearity',
            '-m', '10.0', '-m', '10.1', '-m', '10.2', '-m', '10.3', '-m', '10.4',
            '-m', '10.5', '-m', '10.6', '-m', '10.7', '-m', '10.8', '-m', '10.9',
            '--reference-values', '10.0', '--reference-values', '10.1',
            '--reference-values', '10.2', '--reference-values', '10.3',
            '--reference-values', '10.4', '--reference-values', '10.5',
            '--reference-values', '10.6', '--reference-values', '10.7',
            '--reference-values', '10.8', '--reference-values', '10.9'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['analysis_type'] == 'linearity'
        assert 'r_squared' in data

    def test_stability_with_reference(self, runner):
        """Test stability study with reference value."""
        result = runner.invoke(main, [
            'gage-rr', 'stability',
            '-m', '10.1', '-m', '10.2', '-m', '10.3', '-m', '10.4', '-m', '10.5',
            '--reference-value', '10.0', '--tolerance', '2.0'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['analysis_type'] == 'stability'
        assert 'pct_tolerance' in data


class TestMultivariateExtended:
    """Test multivariate command additional branches."""

    def test_cluster_kmeans_with_data(self, runner, tmp_path):
        """Test K-means clustering with more data."""
        csv_file = tmp_path / "cluster.csv"
        csv_file.write_text("x1,x2\n1,2\n1.5,2.5\n2,3\n2.5,3.5\n3,4\n8,9\n8.5,9.5\n9,10\n9.5,10.5\n10,11\n")
        result = runner.invoke(main, [
            'multivariate', 'cluster', '-f', str(csv_file),
            '--method', 'kmeans', '--n-clusters', '2'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['method'] == 'kmeans'
        assert data['n_clusters'] == 2
        assert 'pct_variance_explained' in data

    def test_pca_with_multiple_columns(self, runner, tmp_path):
        """Test PCA with multiple columns."""
        csv_file = tmp_path / "pca.csv"
        csv_file.write_text("x1,x2,x3,x4\n1,2,3,4\n5,6,7,8\n9,10,11,12\n13,14,15,16\n17,18,19,20\n")
        result = runner.invoke(main, [
            'multivariate', 'pca', '-f', str(csv_file)
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['analysis_type'] == 'pca'
        assert 'eigenvalues' in data
        assert 'loadings' in data

    def test_correlation_matrix_significance(self, runner, tmp_path):
        """Test correlation matrix with significance testing."""
        csv_file = tmp_path / "corr.csv"
        csv_file.write_text("x1,x2,x3\n1,2,3\n4,5,6\n7,8,9\n10,11,12\n13,14,15\n")
        result = runner.invoke(main, [
            'multivariate', 'correlation_matrix', '-f', str(csv_file)
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'p_values' in data
        assert 'correlation_table' in data


class TestRegressionExtended:
    """Test regression command additional branches."""

    def test_regression_with_interactive(self, runner, tmp_path):
        """Test regression with interactive charts."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("x,y\n1,2\n2,4\n3,6\n4,8\n5,10\n")
        result = runner.invoke(main, [
            '--interactive', 'regression', '-f', str(csv_file)
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'interactive_charts' in data

    def test_multiple_regression_with_vif(self, runner, tmp_path):
        """Test multiple regression with VIF diagnostics."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("y,x1,x2,x3\n10,1,2,3\n20,2,4,6\n30,3,6,9\n40,4,8,12\n50,5,10,15\n")
        result = runner.invoke(main, [
            'regression', '-f', str(csv_file),
            '--y-column', 'y', '--x-columns', 'x1', '--x-columns', 'x2', '--x-columns', 'x3',
            '--type', 'multiple'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'vif' in data
        assert 'cooks_distance' in data


class TestTimeseriesExtended:
    """Test timeseries command additional branches."""

    def test_acf_with_more_data(self, runner):
        """Test ACF with more data points."""
        values = [10 + i * 0.5 + (i % 3) * 0.2 for i in range(30)]
        args = ['timeseries', 'acf']
        for v in values:
            args.extend(['-v', str(round(v, 2))])
        args.extend(['--max-lag', '10'])

        result = runner.invoke(main, args)
        assert result.exit_code == 0
        data = get_data(result)
        assert len(data['acf']) > 5
        assert 'suggested_order' in data

    def test_exp_smoothing_with_seasonal(self, runner):
        """Test exponential smoothing with seasonal component."""
        # Quarterly data with seasonal pattern
        values = [100, 120, 110, 130, 105, 125, 115, 135, 110, 130, 120, 140]
        args = ['timeseries', 'exp_smoothing']
        for v in values:
            args.extend(['-v', str(v)])
        args.extend(['--frequency', '4', '--n-forecast', '4'])

        result = runner.invoke(main, args)
        assert result.exit_code == 0
        data = get_data(result)
        assert 'forecast' in data
        assert len(data['forecast']) == 4


class TestReliabilityExtended:
    """Test reliability command additional branches."""

    def test_weibull_with_censored(self, runner):
        """Test Weibull analysis with censored data."""
        result = runner.invoke(main, [
            'reliability', 'weibull',
            '-t', '100', '-t', '200', '-t', '300', '-t', '150', '-t', '250',
            '-t', '350', '-t', '400', '-t', '180', '-t', '280', '-t', '320',
            '-s', '1', '-s', '1', '-s', '1', '-s', '1', '-s', '1',
            '-s', '0', '-s', '0', '-s', '1', '-s', '0', '-s', '1'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['n_censored'] == 3
        assert 'b_lives' in data

    def test_stability_with_confidence(self, runner):
        """Test stability with confidence level."""
        result = runner.invoke(main, [
            'reliability', 'stability',
            '-t', '0', '-t', '3', '-t', '6', '-t', '9', '-t', '12', '-t', '24',
            '-v', '100', '-v', '99.5', '-v', '99', '-v', '98.5', '-v', '98', '-v', '96',
            '--lsl', '90', '--confidence', '0.99'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['confidence'] == 0.99


class TestPowerExtended:
    """Test power command additional branches."""

    def test_t_test_power_given_n(self, runner):
        """Test t-test power calculation given n."""
        result = runner.invoke(main, [
            'power', 't_test', '--effect-size', '0.5', '--n', '30'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'power' in data
        assert data['power'] > 0

    def test_effect_size_eta_squared(self, runner):
        """Test eta-squared effect size."""
        result = runner.invoke(main, [
            'power', 'effect_size', '--metric', 'eta_squared',
            '--ss-effect', '100', '--ss-total', '500'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['metric'] == 'eta_squared'
        assert data['value'] == 0.2


class TestCleanExtended:
    """Test clean command additional branches."""

    def test_winsorize(self, runner):
        """Test winsorize cleaning method."""
        result = runner.invoke(main, [
            'clean', '-v', '10.1', '-v', '10.2', '-v', '10.3', '-v', '10.4', '-v', '10.5',
            '-v', '15.0', '-v', '5.0',  # outliers
            '--method', 'winsorize', '--lower-pct', '0.1', '--upper-pct', '0.9'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['method'] == 'winsorize'

    def test_clip(self, runner):
        """Test clip cleaning method."""
        result = runner.invoke(main, [
            'clean', '-v', '10.1', '-v', '10.2', '-v', '10.3', '-v', '15.0', '-v', '5.0',
            '--method', 'clip', '--lower', '9.0', '--upper', '12.0'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['method'] == 'clip'


class TestTransformExtended:
    """Test transform command additional branches."""

    def test_boxcox_transform(self, runner):
        """Test Box-Cox transformation."""
        result = runner.invoke(main, [
            'transform', '-v', '10.1', '-v', '10.2', '-v', '10.3', '-v', '10.4', '-v', '10.5',
            '--method', 'boxcox'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['method'] == 'boxcox'
        assert 'offset' in data

    def test_rank_transform(self, runner):
        """Test rank transformation."""
        result = runner.invoke(main, [
            'transform', '-v', '10.1', '-v', '10.2', '-v', '10.3', '-v', '10.4', '-v', '10.5',
            '--method', 'rank'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['method'] == 'rank'


class TestDiscoverExtended:
    """Test discover command additional branches."""

    def test_discover_by_category(self, runner):
        """Test discover with category filter."""
        result = runner.invoke(main, ['discover', '--category', 'spc'])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['total_commands'] > 0
        for cmd_name, cmd_info in data['commands'].items():
            assert cmd_info['category'] == 'spc'

    def test_discover_command_with_schema(self, runner):
        """Test discover command with JSON schema."""
        result = runner.invoke(main, ['discover', 'capability', '--json-schema'])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'json_schema' in data


class TestExploreExtended:
    """Test explore command additional branches."""

    def test_explore_with_sheet(self, runner, tmp_path):
        """Test explore with specific sheet."""
        df1 = pd.DataFrame({'x': [1, 2, 3]})
        df2 = pd.DataFrame({'y': [10, 20, 30]})
        excel_file = tmp_path / "test.xlsx"
        with pd.ExcelWriter(excel_file) as writer:
            df1.to_excel(writer, sheet_name='Sheet1', index=False)
            df2.to_excel(writer, sheet_name='Sheet2', index=False)

        result = runner.invoke(main, ['explore', '-f', str(excel_file), '-s', 'Sheet2'])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['sheet'] == 'Sheet2'
        assert 'y' in [c['name'] for c in data['columns']]

    def test_explore_show_more_rows(self, runner, tmp_path):
        """Test explore showing more sample rows."""
        df = pd.DataFrame({'x': range(20)})
        csv_file = tmp_path / "test.csv"
        df.to_csv(csv_file, index=False)

        result = runner.invoke(main, ['explore', '-f', str(csv_file), '-n', '10'])
        assert result.exit_code == 0
        data = get_data(result)
        assert len(data['sample_data']) == 10
