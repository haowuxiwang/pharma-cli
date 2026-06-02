"""Tests with real Excel data files from excel/ directory."""

import pytest
import json
from pathlib import Path
from click.testing import CliRunner
from cli.main import main


@pytest.fixture
def runner():
    """Create a Click test runner."""
    return CliRunner()


# Excel files in the project
EXCEL_DIR = Path(__file__).parent.parent / "excel"
EXCEL_FILES = [
    "低速片重数据.xlsx",
    "低速硬度数据.xlsx",
    "高速片重数据.xlsx",
    "高速硬度数据.xlsx",
    "灌装量数据.xlsx",
    "灌装装量数据.xlsx",
]


def get_data(result):
    """Extract data from wrapped JSON output."""
    output = json.loads(result.output)
    if "data" in output:
        return output["data"]
    return output


def excel_path(filename):
    """Get full path to Excel file."""
    return str(EXCEL_DIR / filename)


class TestExploreRealData:
    """Test explore command with real Excel files."""

    @pytest.mark.parametrize("filename", EXCEL_FILES)
    def test_explore_all_files(self, runner, filename):
        """Test explore can read all Excel files."""
        filepath = excel_path(filename)
        if not Path(filepath).exists():
            pytest.skip(f"File not found: {filename}")

        result = runner.invoke(main, ['explore', '-f', filepath])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'n_rows' in data
        assert 'n_columns' in data
        assert 'columns' in data
        assert data['n_rows'] > 0
        assert data['n_columns'] > 0

    def test_explore_shows_numeric_columns(self, runner):
        """Test that explore identifies numeric columns."""
        filepath = excel_path("灌装量数据.xlsx")
        if not Path(filepath).exists():
            pytest.skip("File not found")

        result = runner.invoke(main, ['explore', '-f', filepath])
        data = get_data(result)
        assert 'numeric_columns' in data
        assert len(data['numeric_columns']) > 0

    def test_explore_shows_sample_data(self, runner):
        """Test that explore shows sample rows."""
        filepath = excel_path("灌装量数据.xlsx")
        if not Path(filepath).exists():
            pytest.skip("File not found")

        result = runner.invoke(main, ['explore', '-f', filepath, '-n', '3'])
        data = get_data(result)
        assert 'sample_data' in data
        assert len(data['sample_data']) == 3


class TestDescriptiveRealData:
    """Test descriptive command with real Excel files."""

    def test_descriptive_single_column_file(self, runner):
        """Test descriptive with single-column Excel file."""
        filepath = excel_path("低速片重数据.xlsx")
        if not Path(filepath).exists():
            pytest.skip("File not found")

        result = runner.invoke(main, ['descriptive', '-f', filepath])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'n' in data
        assert 'mean' in data
        assert 'std' in data
        assert data['n'] > 0

    def test_descriptive_multi_column_file(self, runner):
        """Test descriptive with multi-column Excel file."""
        filepath = excel_path("灌装量数据.xlsx")
        if not Path(filepath).exists():
            pytest.skip("File not found")

        result = runner.invoke(main, ['descriptive', '-f', filepath, '-c', '净重'])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'n' in data
        assert 'mean' in data
        assert data['n'] == 903  # Known row count

    @pytest.mark.parametrize("filename", EXCEL_FILES)
    def test_descriptive_all_files(self, runner, filename):
        """Test descriptive can process all Excel files."""
        filepath = excel_path(filename)
        if not Path(filepath).exists():
            pytest.skip(f"File not found: {filename}")

        result = runner.invoke(main, ['descriptive', '-f', filepath])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'n' in data
        assert 'mean' in data


class TestNormalityRealData:
    """Test normality command with real Excel files."""

    def test_normality_with_real_data(self, runner):
        """Test normality with real Excel data."""
        filepath = excel_path("灌装量数据.xlsx")
        if not Path(filepath).exists():
            pytest.skip("File not found")

        result = runner.invoke(main, ['normality', '-f', filepath, '-c', '净重'])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'shapiro_wilk' in data
        assert 'is_normal' in data

    @pytest.mark.parametrize("filename", EXCEL_FILES)
    def test_normality_all_files(self, runner, filename):
        """Test normality can process all Excel files."""
        filepath = excel_path(filename)
        if not Path(filepath).exists():
            pytest.skip(f"File not found: {filename}")

        result = runner.invoke(main, ['normality', '-f', filepath])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'is_normal' in data


class TestCapabilityRealData:
    """Test capability command with real Excel files."""

    def test_capability_with_spec_limits(self, runner):
        """Test capability with specification limits."""
        filepath = excel_path("灌装量数据.xlsx")
        if not Path(filepath).exists():
            pytest.skip("File not found")

        result = runner.invoke(main, [
            'capability', '-f', filepath, '-c', '净重',
            '--usl', '5.1', '--lsl', '4.9'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'cp' in data
        assert 'cpk' in data
        assert 'rating' in data

    def test_capability_with_boxcox(self, runner):
        """Test capability with Box-Cox transformation."""
        filepath = excel_path("灌装量数据.xlsx")
        if not Path(filepath).exists():
            pytest.skip("File not found")

        result = runner.invoke(main, [
            'capability', '-f', filepath, '-c', '净重',
            '--usl', '5.1', '--lsl', '4.9', '--type', 'boxcox'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'cp' in data


class TestControlChartRealData:
    """Test control chart command with real Excel files."""

    def test_imr_chart(self, runner):
        """Test I-MR chart with real data."""
        filepath = excel_path("灌装量数据.xlsx")
        if not Path(filepath).exists():
            pytest.skip("File not found")

        result = runner.invoke(main, ['control-chart', 'imr', '-f', filepath, '-c', '净重'])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'chart_type' in data
        assert data['chart_type'] == 'imr'
        assert 'chart' in data

    @pytest.mark.parametrize("filename", EXCEL_FILES)
    def test_control_chart_all_files(self, runner, filename):
        """Test control chart can process all Excel files."""
        filepath = excel_path(filename)
        if not Path(filepath).exists():
            pytest.skip(f"File not found: {filename}")

        result = runner.invoke(main, ['control-chart', 'imr', '-f', filepath])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'chart_type' in data


class TestRegressionRealData:
    """Test regression command with real Excel files."""

    def test_regression_with_excel(self, runner):
        """Test regression with Excel file."""
        filepath = excel_path("灌装量数据.xlsx")
        if not Path(filepath).exists():
            pytest.skip("File not found")

        result = runner.invoke(main, [
            'regression', '-f', filepath,
            '--x-column', '皮重', '--y-column', '净重'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'regression_type' in data
        assert 'r_squared' in data


class TestCorrelationRealData:
    """Test correlation command with real Excel files."""

    def test_correlation_with_excel(self, runner):
        """Test correlation with Excel file."""
        filepath = excel_path("灌装量数据.xlsx")
        if not Path(filepath).exists():
            pytest.skip("File not found")

        result = runner.invoke(main, [
            'correlation', '-f', filepath,
            '--x-column', '皮重', '--y-column', '净重'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'method' in data
        assert 'correlation' in data


class TestMultivariateRealData:
    """Test multivariate command with real Excel files."""

    def test_pca_with_excel(self, runner):
        """Test PCA with Excel file."""
        filepath = excel_path("灌装量数据.xlsx")
        if not Path(filepath).exists():
            pytest.skip("File not found")

        result = runner.invoke(main, [
            'multivariate', 'pca', '-f', filepath,
            '-c', '皮重', '-c', '总重', '-c', '净重'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'analysis_type' in data
        assert data['analysis_type'] == 'pca'

    def test_correlation_matrix_with_excel(self, runner):
        """Test correlation matrix with Excel file."""
        filepath = excel_path("灌装量数据.xlsx")
        if not Path(filepath).exists():
            pytest.skip("File not found")

        result = runner.invoke(main, [
            'multivariate', 'correlation_matrix', '-f', filepath,
            '-c', '皮重', '-c', '总重', '-c', '净重'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'correlation_matrix' in data


class TestCleanRealData:
    """Test clean command with real Excel files."""

    def test_clean_with_real_data(self, runner):
        """Test clean with real Excel data."""
        filepath = excel_path("灌装量数据.xlsx")
        if not Path(filepath).exists():
            pytest.skip("File not found")

        result = runner.invoke(main, [
            'clean', '-f', filepath, '-c', '净重', '--method', 'drop'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'method' in data
        assert 'n_original' in data
