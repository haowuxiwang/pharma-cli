"""Coverage boost tests - targeting specific uncovered lines."""

import pytest
import json
import pandas as pd
from click.testing import CliRunner
from cli.main import main
from cli.commands.utils import _load_excel, _load_csv, _extract_excel_column, output
from cli.reports import ReportGenerator


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


class TestUtilsCoverage:
    """Test utils.py uncovered paths."""

    def test_load_excel_numeric_column_match(self, tmp_path):
        """Test Excel with numeric column name match."""
        import pandas as pd
        df = pd.DataFrame({1.5: [10, 20, 30], 2.5: [40, 50, 60]})
        excel_file = tmp_path / "test.xlsx"
        df.to_excel(excel_file, index=False)
        result = _load_excel(excel_file, '1.5')
        assert 'values' in result

    def test_load_csv_with_empty_cells(self, tmp_path):
        """Test CSV with empty cells."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("x,y\n1,10\n,20\n3,\n4,40\n")
        content = csv_file.read_text()
        result = _load_csv(csv_file, content, 'x')
        assert 'values' in result

    def test_extract_excel_column_by_numeric_name(self, tmp_path):
        """Test extracting Excel column by numeric name."""
        import pandas as pd
        df = pd.DataFrame({100: [1, 2, 3], 200: [4, 5, 6]})
        result = _extract_excel_column(df, '100', "test.xlsx")
        assert result == [1, 2, 3]


class TestGageRrCoverage:
    """Test gage-rr uncovered paths."""

    def test_crossed_with_one_replicate(self, runner):
        """Test crossed Gage R&R with exactly 1 replicate."""
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
        assert data['has_interaction'] is False

    def test_stability_with_time_points(self, runner):
        """Test stability study with time points."""
        result = runner.invoke(main, [
            'gage-rr', 'stability',
            '-m', '10.1', '-m', '10.2', '-m', '10.3', '-m', '10.4', '-m', '10.5',
            '--tolerance', '2.0'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'pct_tolerance' in data


class TestMultivariateCoverage:
    """Test multivariate uncovered paths."""

    def test_pca_with_all_numeric(self, runner, tmp_path):
        """Test PCA with all numeric columns."""
        csv_file = tmp_path / "pca.csv"
        csv_file.write_text("a,b,c\n1,2,3\n4,5,6\n7,8,9\n10,11,12\n13,14,15\n")
        result = runner.invoke(main, [
            'multivariate', 'pca', '-f', str(csv_file)
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['n_variables'] == 3

    def test_cluster_kmeans_with_variance(self, runner, tmp_path):
        """Test K-means clustering with variance explained."""
        csv_file = tmp_path / "cluster.csv"
        csv_file.write_text("x1,x2\n1,2\n1.5,2.5\n2,3\n2.5,3.5\n3,4\n8,9\n8.5,9.5\n9,10\n9.5,10.5\n10,11\n")
        result = runner.invoke(main, [
            'multivariate', 'cluster', '-f', str(csv_file),
            '--method', 'kmeans', '--n-clusters', '2'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'pct_variance_explained' in data


class TestRegressionCoverage:
    """Test regression uncovered paths."""

    def test_regression_with_all_types(self, runner, tmp_path):
        """Test regression with all regression types."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("x,y\n1,2\n2,4\n3,6\n4,8\n5,10\n")

        for reg_type in ['linear', 'quadratic', 'polynomial']:
            result = runner.invoke(main, [
                'regression', '-f', str(csv_file), '--type', reg_type
            ])
            assert result.exit_code == 0
            data = get_data(result)
            assert data['regression_type'] == reg_type

    def test_multiple_regression_all_diagnostics(self, runner, tmp_path):
        """Test multiple regression with all diagnostics."""
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


class TestTimeseriesCoverage:
    """Test timeseries uncovered paths."""

    def test_exp_smoothing_with_all_params(self, runner):
        """Test exponential smoothing with all parameters."""
        values = [100, 120, 110, 130, 105, 125, 115, 135, 110, 130, 120, 140]
        args = ['timeseries', 'exp_smoothing']
        for v in values:
            args.extend(['-v', str(v)])
        args.extend(['--frequency', '4', '--n-forecast', '4', '--method', 'holt_winters'])

        result = runner.invoke(main, args)
        assert result.exit_code == 0
        data = get_data(result)
        assert 'parameters' in data
        assert 'metrics' in data

    def test_acf_with_significant_lags(self, runner):
        """Test ACF with significant lags."""
        # Create data with clear autocorrelation
        values = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25]
        args = ['timeseries', 'acf']
        for v in values:
            args.extend(['-v', str(v)])
        args.extend(['--max-lag', '5'])

        result = runner.invoke(main, args)
        assert result.exit_code == 0
        data = get_data(result)
        assert 'significant_acf_lags' in data


class TestReliabilityCoverage:
    """Test reliability uncovered paths."""

    def test_weibull_with_all_outputs(self, runner):
        """Test Weibull with all output fields."""
        result = runner.invoke(main, [
            'reliability', 'weibull',
            '-t', '100', '-t', '200', '-t', '300', '-t', '150', '-t', '250',
            '-s', '1', '-s', '1', '-s', '1', '-s', '1', '-s', '1',
            '--time', '200'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'b_lives' in data
        assert 'mttf' in data
        assert 'failure_pattern' in data
        assert 'reliability_at_time' in data

    def test_stability_with_all_outputs(self, runner):
        """Test stability with all output fields."""
        result = runner.invoke(main, [
            'reliability', 'stability',
            '-t', '0', '-t', '3', '-t', '6', '-t', '9', '-t', '12', '-t', '24',
            '-v', '100', '-v', '99.5', '-v', '99', '-v', '98.5', '-v', '98', '-v', '96',
            '--lsl', '90', '--confidence', '0.99'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'shelf_life' in data
        assert 'regression' in data
        assert 'confidence' in data


class TestAdvancedCoverage:
    """Test advanced uncovered paths."""

    def test_exact_test_with_significant(self, runner):
        """Test Fisher's exact test with significant result."""
        result = runner.invoke(main, [
            'advanced', 'exact_test',
            '--observed-matrix', '[[20,5],[5,20]]'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['fisher']['p_value'] < 0.05

    def test_mcnemar_with_significant(self, runner):
        """Test McNemar with significant result."""
        result = runner.invoke(main, [
            'advanced', 'mcnemar',
            '--observed-matrix', '[[1,20],[30,5]]'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'statistic' in data
        assert 'p_value' in data


class TestControlChartCoverage:
    """Test control chart uncovered paths."""

    def test_all_chart_types(self, runner):
        """Test all control chart types."""
        chart_types = ['imr', 'xbar', 'r']
        for chart_type in chart_types:
            result = runner.invoke(main, [
                'control-chart', chart_type,
                '-v', '10.2', '-v', '10.5', '-v', '10.1', '-v', '10.3', '-v', '10.4',
                '-v', '10.6', '-v', '10.3', '-v', '10.5', '-v', '10.2', '-v', '10.4'
            ])
            assert result.exit_code == 0
            data = get_data(result)
            assert data['chart_type'] == chart_type

    def test_p_chart_with_sample_size(self, runner):
        """Test p chart with sample size."""
        result = runner.invoke(main, [
            'control-chart', 'p',
            '-v', '10', '-v', '12', '-v', '8', '-v', '15', '-v', '11',
            '--sample-size', '100'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['chart_type'] == 'p'


class TestExploreCoverage:
    """Test explore uncovered paths."""

    def test_explore_with_all_column_types(self, runner, tmp_path):
        """Test explore with all column types."""
        df = pd.DataFrame({
            'int_col': [1, 2, 3],
            'float_col': [1.1, 2.2, 3.3],
            'str_col': ['a', 'b', 'c'],
            'date_col': pd.to_datetime(['2024-01-01', '2024-01-02', '2024-01-03'])
        })
        csv_file = tmp_path / "test.csv"
        df.to_csv(csv_file, index=False)
        result = runner.invoke(main, ['explore', '-f', str(csv_file)])
        assert result.exit_code == 0
        data = get_data(result)
        assert len(data['columns']) == 4
        assert len(data['numeric_columns']) == 2


class TestReportsCoverageExtended:
    """Tests to improve cli/reports.py coverage."""

    def test_generate_control_chart_report(self):
        """Test control chart report generation."""
        generator = ReportGenerator()
        data = {
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
        result = generator.generate_control_chart_report(data)
        assert isinstance(result, str)
        assert '<html>' in result.lower()

    def test_generate_regression_report(self):
        """Test regression report generation."""
        generator = ReportGenerator()
        data = {
            'regression_type': 'linear',
            'r_squared': 0.95,
            'adj_r_squared': 0.94,
            'coefficients': {
                'intercept': {'estimate': 1.0, 'std_error': 0.1, 't_value': 10.0, 'p_value': 0.001},
                'x1': {'estimate': 2.0, 'std_error': 0.2, 't_value': 10.0, 'p_value': 0.001}
            },
            'f_statistic': 100.0,
            'f_p_value': 0.001,
            'n': 10,
            'formula': 'y ~ x1',
            'residual_std_error': 0.5,
            'residuals': {'mean': 0.0, 'std': 0.5, 'shapiro_p': 0.5, 'normal': True}
        }
        result = generator.generate_regression_report(data)
        assert isinstance(result, str)

    def test_generate_report_dispatch(self):
        """Test generate_report method dispatch."""
        generator = ReportGenerator()
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
        result = generator.generate_report('descriptive', data)
        assert isinstance(result, str)

    def test_generate_report_unsupported_type(self):
        """Test generate_report with unsupported type."""
        generator = ReportGenerator()
        data = {'n': 5}
        with pytest.raises(ValueError, match="Unsupported analysis type"):
            generator.generate_report('unsupported_type', data)

    def test_generate_report_with_charts(self):
        """Test generate_report with charts dict."""
        generator = ReportGenerator()
        data = {
            'shapiro_wilk': {'statistic': 0.95, 'p_value': 0.5, 'is_normal': True},
            'anderson_darling': {'statistic': 0.3, 'p_value': 0.6},
            'lilliefors': {'statistic': 0.05, 'p_value': 0.7},
            'is_normal': True,
            'interpretation': 'Data is normally distributed'
        }
        charts = {'histogram': '<div>chart</div>'}
        result = generator.generate_report('normality', data, charts)
        assert isinstance(result, str)


class TestGageRRCoverageExtended:
    """Tests to improve gage_rr.py coverage."""

    def test_gage_rr_from_file(self, runner, tmp_path):
        """Test gage-rr from JSON file."""
        data = {
            'measurements': [10.1, 10.2, 10.3, 10.1, 10.2, 10.3],
            'parts': ['P1', 'P1', 'P1', 'P2', 'P2', 'P2'],
            'operators': ['O1', 'O1', 'O1', 'O1', 'O1', 'O1']
        }
        json_file = tmp_path / "msa.json"
        json_file.write_text(json.dumps(data))
        result = runner.invoke(main, [
            'gage-rr', 'crossed', '-f', str(json_file)
        ])
        assert result.exit_code == 0

    def test_gage_rr_nested(self, runner):
        """Test nested gage-rr."""
        result = runner.invoke(main, [
            'gage-rr', 'nested',
            '-m', '10.1', '-m', '10.2', '-m', '10.3',
            '-p', 'P1', '-p', 'P1', '-p', 'P1',
            '-o', 'O1', '-o', 'O1', '-o', 'O1'
        ])
        assert result.exit_code == 0

    def test_gage_rr_bias(self, runner):
        """Test bias study."""
        result = runner.invoke(main, [
            'gage-rr', 'bias',
            '-m', '10.1', '-m', '10.2', '-m', '10.3',
            '--reference-value', '10.0'
        ])
        assert result.exit_code == 0

    def test_gage_rr_linearity(self, runner):
        """Test linearity study."""
        result = runner.invoke(main, [
            'gage-rr', 'linearity',
            '-m', '10.1', '-m', '10.2', '-m', '10.3',
            '--reference-values', '10.0', '--reference-values', '11.0', '--reference-values', '12.0'
        ])
        assert result.exit_code == 0

    def test_gage_rr_stability_with_tolerance(self, runner):
        """Test stability study with tolerance."""
        result = runner.invoke(main, [
            'gage-rr', 'stability',
            '-m', '10.1', '-m', '10.2', '-m', '10.3', '-m', '10.4', '-m', '10.5',
            '--tolerance', '2.0'
        ])
        assert result.exit_code == 0

    def test_gage_rr_attribute_error(self, runner):
        """Test attribute analysis requires file."""
        result = runner.invoke(main, ['gage-rr', 'attribute'])
        assert result.exit_code != 0
        assert 'JSON file' in result.output


class TestMultivariateCoverageExtended:
    """Tests to improve multivariate.py coverage."""

    def test_cluster_from_csv(self, runner, tmp_path):
        """Test clustering from CSV."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("x1,x2,x3\n1,2,3\n4,5,6\n7,8,9\n10,11,12\n13,14,15\n")
        result = runner.invoke(main, [
            'multivariate', 'cluster', '-f', str(csv_file),
            '--method', 'kmeans', '--n-clusters', '2'
        ])
        assert result.exit_code == 0

    def test_discriminant_from_csv(self, runner, tmp_path):
        """Test discriminant analysis from CSV."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("x1,x2,group\n1,2,A\n3,4,A\n5,6,B\n7,8,B\n")
        result = runner.invoke(main, [
            'multivariate', 'discriminant', '-f', str(csv_file),
            '-g', 'group'
        ])
        assert result.exit_code == 0

    def test_discriminant_no_groups_error(self, runner, tmp_path):
        """Test discriminant without groups fails."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("x1,x2\n1,2\n3,4\n")
        result = runner.invoke(main, [
            'multivariate', 'discriminant', '-f', str(csv_file)
        ])
        assert result.exit_code != 0
        assert 'group' in result.output.lower()

    def test_pca_with_columns(self, runner, tmp_path):
        """Test PCA with specific columns."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("x1,x2,x3,y\n1,2,3,4\n5,6,7,8\n")
        result = runner.invoke(main, [
            'multivariate', 'pca', '-f', str(csv_file),
            '-c', 'x1', '-c', 'x2'
        ])
        assert result.exit_code == 0

    def test_no_file_error(self, runner):
        """Test multivariate without file fails."""
        result = runner.invoke(main, ['multivariate', 'pca'])
        assert result.exit_code != 0


class TestUtilsVersionCoverage:
    """Tests to verify version in output."""

    def test_output_version(self, capsys):
        """Test output includes correct version."""
        output({"test": "data"})
        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result['version'] == '0.4.0'

    def test_output_error_version(self, capsys):
        """Test error output includes correct version."""
        output({"error": True, "error_type": "TEST", "message": "test"})
        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result['version'] == '0.4.0'


class TestDiscoverCoverageExtended:
    """Tests to improve discover.py coverage."""

    def test_discover_timeseries(self, runner):
        """Test discover for timeseries command."""
        result = runner.invoke(main, ['discover', 'timeseries'])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['command'] == 'timeseries'

    def test_discover_power(self, runner):
        """Test discover for power command."""
        result = runner.invoke(main, ['discover', 'power'])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['command'] == 'power'

    def test_discover_all_categories(self, runner):
        """Test discover with all categories."""
        for cat in ['basic', 'spc', 'hypothesis', 'regression', 'doe', 'msa', 'data', 'report', 'advanced']:
            result = runner.invoke(main, ['discover', '--category', cat])
            assert result.exit_code == 0

    def test_discover_unknown_command(self, runner):
        """Test discover with unknown command."""
        result = runner.invoke(main, ['discover', 'nonexistent'])
        assert result.exit_code != 0


class TestTimeseriesCoverageExtended:
    """Tests to improve timeseries.py coverage (80% -> 95%)."""

    def test_arima_with_order(self, runner):
        """Test ARIMA with explicit order."""
        result = runner.invoke(main, [
            'timeseries', 'arima',
            '-v', '10', '-v', '12', '-v', '11', '-v', '13', '-v', '14',
            '-v', '12', '-v', '15', '-v', '13', '-v', '16', '-v', '14',
            '--order', '1', '--order', '1', '--order', '1',
            '--n-forecast', '3'
        ])
        assert result.exit_code == 0

    def test_arima_invalid_order(self, runner):
        """Test ARIMA with invalid order length."""
        result = runner.invoke(main, [
            'timeseries', 'arima',
            '-v', '10', '-v', '12', '-v', '11',
            '--order', '1', '--order', '1'
        ])
        assert result.exit_code != 0
        assert 'exactly 3 values' in result.output

    def test_decomposition(self, runner):
        """Test decomposition analysis."""
        result = runner.invoke(main, [
            'timeseries', 'decomposition',
            '-v', '10', '-v', '12', '-v', '11', '-v', '13', '-v', '14',
            '-v', '12', '-v', '15', '-v', '13', '-v', '16', '-v', '14',
            '--frequency', '4'
        ])
        assert result.exit_code == 0

    def test_acf_with_max_lag(self, runner):
        """Test ACF with max lag parameter."""
        result = runner.invoke(main, [
            'timeseries', 'acf',
            '-v', '10', '-v', '11', '-v', '12', '-v', '13', '-v', '14',
            '--max-lag', '3'
        ])
        assert result.exit_code == 0

    def test_from_file(self, runner, tmp_path):
        """Test timeseries from file."""
        csv_file = tmp_path / "ts.csv"
        csv_file.write_text("value\n10\n12\n11\n13\n14\n12\n15\n13\n16\n14\n")
        result = runner.invoke(main, [
            'timeseries', 'exp_smoothing', '-f', str(csv_file), '-c', 'value'
        ])
        assert result.exit_code == 0

    def test_no_data_error(self, runner):
        """Test timeseries without data fails."""
        result = runner.invoke(main, ['timeseries', 'exp_smoothing'])
        assert result.exit_code != 0


class TestAdvancedCoverageExtended:
    """Tests to improve advanced.py coverage (81% -> 95%)."""

    def test_mixed_effects(self, runner, tmp_path):
        """Test mixed effects model from file."""
        data = {
            "response": [10, 12, 11, 13, 14, 15],
            "subject": [1, 1, 2, 2, 3, 3],
            "treatment": ["A", "B", "A", "B", "A", "B"]
        }
        json_file = tmp_path / "mixed.json"
        json_file.write_text(json.dumps(data))
        result = runner.invoke(main, [
            'advanced', 'mixed_effects', '-f', str(json_file),
            '--response', 'response', '--fixed-effects', 'treatment',
            '--random-effects', 'subject'
        ])
        assert result.exit_code == 0

    def test_mixed_effects_no_response_error(self, runner):
        """Test mixed effects without response fails."""
        result = runner.invoke(main, ['advanced', 'mixed_effects'])
        assert result.exit_code != 0

    def test_cox_regression(self, runner, tmp_path):
        """Test Cox regression from file."""
        data = {
            "time": [100, 200, 300, 150, 250],
            "status": [1, 1, 0, 1, 1],
            "treatment": ["A", "B", "A", "B", "A"]
        }
        json_file = tmp_path / "cox.json"
        json_file.write_text(json.dumps(data))
        result = runner.invoke(main, [
            'advanced', 'cox_regression', '-f', str(json_file),
            '--time-column', 'time', '--status-column', 'status',
            '--covariates', 'treatment'
        ])
        assert result.exit_code == 0

    def test_cox_regression_no_time_error(self, runner):
        """Test Cox regression without time column fails."""
        result = runner.invoke(main, ['advanced', 'cox_regression'])
        assert result.exit_code != 0


class TestNonparametricCoverageExtended:
    """Tests to improve nonparametric.py coverage (81% -> 95%)."""

    def test_mann_whitney_no_x_error(self, runner):
        """Test Mann-Whitney without --x fails."""
        result = runner.invoke(main, [
            'nonparametric', 'mann_whitney', '--y', '10', '--y', '11'
        ])
        assert result.exit_code != 0
        assert '--x and --y required' in result.output

    def test_kruskal_wallis_no_groups_error(self, runner):
        """Test Kruskal-Wallis without --groups fails."""
        result = runner.invoke(main, ['nonparametric', 'kruskal_wallis'])
        assert result.exit_code != 0
        assert '--groups required' in result.output

    def test_chi_square_no_observed_error(self, runner):
        """Test chi-square without --observed fails."""
        result = runner.invoke(main, ['nonparametric', 'chi_square'])
        assert result.exit_code != 0
        assert '--observed required' in result.output

    def test_chi_square_independence_no_matrix_error(self, runner):
        """Test chi-square independence without matrix fails."""
        result = runner.invoke(main, [
            'nonparametric', 'chi_square', '--chi-type', 'independence'
        ])
        assert result.exit_code != 0
        assert '--observed-matrix required' in result.output

    def test_friedman_no_groups_error(self, runner):
        """Test Friedman without --groups fails."""
        result = runner.invoke(main, ['nonparametric', 'friedman'])
        assert result.exit_code != 0
        assert '--groups required' in result.output

    def test_chi_square_with_expected(self, runner):
        """Test chi-square with expected frequencies."""
        result = runner.invoke(main, [
            'nonparametric', 'chi_square',
            '--observed', '50', '--observed', '30', '--observed', '20',
            '--expected', '40', '--expected', '35', '--expected', '25'
        ])
        assert result.exit_code == 0


class TestControlChartCoverageExtended:
    """Tests to improve control_chart.py coverage (85% -> 95%)."""

    def test_interactive_chart(self, runner):
        """Test control chart with --interactive flag."""
        result = runner.invoke(main, [
            '--interactive', 'control-chart', 'imr',
            '-v', '10.2', '-v', '10.5', '-v', '10.1', '-v', '10.3', '-v', '10.4'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'interactive_chart' in data

    def test_cusum_chart(self, runner):
        """Test CUSUM chart."""
        result = runner.invoke(main, [
            'control-chart', 'cusum',
            '-v', '10.2', '-v', '10.5', '-v', '10.1', '-v', '10.3', '-v', '10.4',
            '--target', '10.3', '--cusum-k', '0.5', '--cusum-h', '5'
        ])
        assert result.exit_code == 0

    def test_ewma_chart_lambda_zero(self, runner):
        """Test EWMA chart with lambda=0."""
        result = runner.invoke(main, [
            'control-chart', 'ewma',
            '-v', '10.2', '-v', '10.5', '-v', '10.1', '-v', '10.3', '-v', '10.4',
            '--ewma-lambda', '0'
        ])
        assert result.exit_code == 0


class TestUtilsStdinCoverageExtended:
    """Tests to improve utils.py stdin and Excel coverage."""

    def test_load_data_stdin_json_with_cleaning(self, runner):
        """Test load_data from stdin with JSON needing cleaning."""
        json_data = json.dumps({"values": [10.2, None, 10.5, float('nan'), 10.1]})
        result = runner.invoke(main, ['descriptive'], input=json_data)
        assert result.exit_code == 0

    def test_load_data_stdin_plain_text(self, runner):
        """Test load_data from stdin with plain text."""
        text_data = "10.2\n10.5\n10.1\n"
        result = runner.invoke(main, ['descriptive'], input=text_data)
        assert result.exit_code == 0

    def test_load_excel_with_datetime_column(self, runner, tmp_path):
        """Test Excel loading with datetime column."""
        df = pd.DataFrame({
            'date': pd.to_datetime(['2024-01-01', '2024-01-02', '2024-01-03']),
            'value': [10.2, 10.5, 10.1]
        })
        excel_file = tmp_path / "datetime.xlsx"
        df.to_excel(excel_file, index=False)
        result = runner.invoke(main, ['descriptive', '-f', str(excel_file)])
        assert result.exit_code == 0

    def test_load_excel_no_sheet(self, runner, tmp_path):
        """Test Excel loading without sheet (default first sheet)."""
        df = pd.DataFrame({'x': [10.2, 10.5, 10.1]})
        excel_file = tmp_path / "test.xlsx"
        df.to_excel(excel_file, index=False)
        result = runner.invoke(main, ['descriptive', '-f', str(excel_file)])
        assert result.exit_code == 0
