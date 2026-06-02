"""Final coverage improvement tests."""

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


class TestReportsExtended:
    """Test reports module additional coverage."""

    def test_generate_control_chart_report(self, runner):
        """Test control chart report generation."""
        result = runner.invoke(main, [
            '--report', 'control-chart', 'imr',
            '-v', '10.2', '-v', '10.5', '-v', '10.1', '-v', '10.3', '-v', '10.4'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        # report flag with control-chart just runs the command
        assert 'chart_type' in data

    def test_generate_regression_report(self, runner, tmp_path):
        """Test regression report generation."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("x,y\n1,2\n2,4\n3,6\n4,8\n5,10\n")
        result = runner.invoke(main, [
            '--report', 'regression', '-f', str(csv_file)
        ])
        assert result.exit_code == 0
        data = get_data(result)
        # report flag with regression just runs the command
        assert 'regression_type' in data


class TestTimeseriesExtended:
    """Test timeseries additional coverage."""

    def test_decomposition(self, runner):
        """Test seasonal decomposition."""
        # Need at least 2 full seasonal cycles
        values = [100, 120, 110, 130, 105, 125, 115, 135, 110, 130, 120, 140,
                  102, 122, 112, 132, 107, 127, 117, 137, 112, 132, 122, 142]
        args = ['timeseries', 'decomposition']
        for v in values:
            args.extend(['-v', str(v)])
        args.extend(['--frequency', '12'])

        result = runner.invoke(main, args)
        assert result.exit_code == 0
        data = get_data(result)
        assert data['analysis_type'] == 'decomposition'
        assert 'trend' in data
        assert 'seasonal' in data

    def test_acf_with_different_method(self, runner):
        """Test ACF with different method."""
        values = [10 + i * 0.5 for i in range(20)]
        args = ['timeseries', 'acf']
        for v in values:
            args.extend(['-v', str(round(v, 2))])
        args.extend(['--max-lag', '5'])

        result = runner.invoke(main, args)
        assert result.exit_code == 0
        data = get_data(result)
        assert 'acf' in data
        assert 'pacf' in data


class TestNonparametricExtended:
    """Test nonparametric additional coverage."""

    def test_chi_square_with_expected(self, runner):
        """Test chi-square with expected frequencies."""
        result = runner.invoke(main, [
            'nonparametric', 'chi_square',
            '--observed', '50', '--observed', '30', '--observed', '20',
            '--expected', '33.33', '--expected', '33.33', '--expected', '33.34'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['test_type'] == 'chi_square'

    def test_kruskal_wallis_with_more_groups(self, runner):
        """Test Kruskal-Wallis with more groups."""
        result = runner.invoke(main, [
            'nonparametric', 'kruskal_wallis',
            '-g', '[10.2,10.5,10.1]', '-g', '[11.3,11.5,11.1]',
            '-g', '[12.1,12.3,12.5]', '-g', '[13.1,13.3,13.5]'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'n_groups' in data
        assert 'statistic' in data


class TestGageRrExtended:
    """Test gage-rr additional coverage."""

    def test_crossed_without_tolerance(self, runner):
        """Test crossed Gage R&R without tolerance."""
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
            '-o', 'O1', '-o', 'O2', '-o', 'O3'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['analysis_type'] == 'crossed_gage_rr'
        assert data['tolerance']['grr'] is None


class TestMultivariateExtended:
    """Test multivariate additional coverage."""

    def test_pca_with_columns(self, runner, tmp_path):
        """Test PCA with specific columns."""
        csv_file = tmp_path / "pca.csv"
        csv_file.write_text("a,b,c,d\n1,2,3,4\n5,6,7,8\n9,10,11,12\n13,14,15,16\n17,18,19,20\n")
        result = runner.invoke(main, [
            'multivariate', 'pca', '-f', str(csv_file),
            '-c', 'a', '-c', 'b', '-c', 'c'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['n_variables'] == 3

    def test_cluster_hierarchical_with_method(self, runner, tmp_path):
        """Test hierarchical clustering with specific method."""
        csv_file = tmp_path / "cluster.csv"
        csv_file.write_text("x1,x2\n1,2\n1.5,2.5\n2,3\n8,9\n8.5,9.5\n9,10\n")
        result = runner.invoke(main, [
            'multivariate', 'cluster', '-f', str(csv_file),
            '--method', 'hierarchical', '--n-clusters', '2'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['method'] == 'hierarchical'
        assert 'cophenetic_correlation' in data


class TestReliabilityExtended:
    """Test reliability additional coverage."""

    def test_weibull_with_time_point(self, runner):
        """Test Weibull with specific time point."""
        result = runner.invoke(main, [
            'reliability', 'weibull',
            '-t', '100', '-t', '200', '-t', '300', '-t', '150', '-t', '250',
            '-s', '1', '-s', '1', '-s', '1', '-s', '1', '-s', '1',
            '--time', '200'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'reliability_at_time' in data
        assert data['reliability_at_time'] > 0

    def test_distribution_fitting_with_more_data(self, runner):
        """Test distribution fitting with more data."""
        result = runner.invoke(main, [
            'reliability', 'distribution',
            '-t', '100', '-t', '150', '-t', '200', '-t', '250', '-t', '300',
            '-t', '350', '-t', '400', '-t', '450', '-t', '500', '-t', '550',
            '-s', '1', '-s', '1', '-s', '1', '-s', '1', '-s', '1',
            '-s', '1', '-s', '1', '-s', '1', '-s', '1', '-s', '1'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'best_distribution' in data
        assert 'fits' in data


class TestAdvancedExtended:
    """Test advanced additional coverage."""

    def test_exact_test_with_different_data(self, runner):
        """Test Fisher's exact test with different data."""
        result = runner.invoke(main, [
            'advanced', 'exact_test',
            '--observed-matrix', '[[8,2],[3,7]]'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'fisher' in data
        assert 'p_value' in data['fisher']

    def test_cochran_q_significant(self, runner):
        """Test Cochran's Q with significant result."""
        result = runner.invoke(main, [
            'advanced', 'cochran_q',
            '--data-matrix', '[[1,1,1],[1,1,1],[1,1,0],[0,0,1],[0,0,0]]'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'statistic' in data


class TestControlChartExtended:
    """Test control chart additional coverage."""

    def test_p_chart(self, runner):
        """Test p chart for proportion data."""
        result = runner.invoke(main, [
            'control-chart', 'p',
            '-v', '10', '-v', '12', '-v', '8', '-v', '15', '-v', '11',
            '--sample-size', '100'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['chart_type'] == 'p'

    def test_c_chart(self, runner):
        """Test c chart for count data."""
        result = runner.invoke(main, [
            'control-chart', 'c',
            '-v', '3', '-v', '5', '-v', '2', '-v', '4', '-v', '6'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['chart_type'] == 'c'


class TestExploreExtended:
    """Test explore additional coverage."""

    def test_explore_with_numeric_column_name(self, runner, tmp_path):
        """Test explore with numeric column name."""
        df = pd.DataFrame({1: [1, 2, 3], 2: [10, 20, 30]})
        excel_file = tmp_path / "test.xlsx"
        df.to_excel(excel_file, index=False)
        result = runner.invoke(main, ['explore', '-f', str(excel_file)])
        assert result.exit_code == 0
        data = get_data(result)
        assert len(data['columns']) == 2

    def test_explore_with_missing_values(self, runner, tmp_path):
        """Test explore with missing values."""
        df = pd.DataFrame({'x': [1, None, 3, None, 5], 'y': [10, 20, None, 40, 50]})
        csv_file = tmp_path / "test.csv"
        df.to_csv(csv_file, index=False)
        result = runner.invoke(main, ['explore', '-f', str(csv_file)])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['columns'][0]['n_missing'] == 2
        assert data['columns'][1]['n_missing'] == 1


class TestRunCommand:
    """Test run command."""

    def test_run_with_data(self, runner, tmp_path):
        """Test run command with data."""
        # Create a simple R script
        r_script = tmp_path / "test.R"
        r_script.write_text('library(jsonlite)\ninput <- fromJSON(file("stdin"))\ncat(toJSON(list(n=length(input$values), mean=mean(input$values)), auto_unbox=TRUE))\n')
        result = runner.invoke(main, [
            'run', str(r_script), '-d', '{"values": [1, 2, 3, 4, 5]}'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['n'] == 5
        assert data['mean'] == 3.0
