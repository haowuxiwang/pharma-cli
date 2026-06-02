"""Extended tests for correlation and regression commands."""

import pytest
import json
import pandas as pd
from click.testing import CliRunner
from cli.main import main
from cli.commands.correlation import _load_xy_from_file, _load_xy_from_excel, _load_xy_from_csv, _load_xy_from_text, _extract_column


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


class TestCorrelationLoadFunctions:
    """Test correlation module load functions."""

    def test_load_xy_from_excel(self, tmp_path):
        """Test loading X/Y from Excel."""
        df = pd.DataFrame({'x': [1, 2, 3, 4, 5], 'y': [2, 4, 6, 8, 10]})
        excel_file = tmp_path / "test.xlsx"
        df.to_excel(excel_file, index=False)
        result = _load_xy_from_excel(excel_file, 'x', 'y')
        assert 'x' in result
        assert 'y' in result
        assert len(result['x']) == 5

    def test_load_xy_from_csv(self, tmp_path):
        """Test loading X/Y from CSV."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("x,y\n1,2\n2,4\n3,6\n")
        result = _load_xy_from_csv(csv_file, 'x', 'y')
        assert 'x' in result
        assert 'y' in result

    def test_load_xy_from_text(self, tmp_path):
        """Test loading X/Y from text file."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("1 2\n3 4\n5 6\n")
        result = _load_xy_from_text(txt_file)
        assert 'x' in result
        assert 'y' in result

    def test_extract_column_by_name(self):
        """Test extracting column by name."""
        df = pd.DataFrame({'x': [1, 2, 3], 'y': [10, 20, 30]})
        result = _extract_column(df, 'y', 'y')
        assert result == [10, 20, 30]

    def test_extract_column_by_index(self):
        """Test extracting column by index."""
        df = pd.DataFrame({'a': [1, 2, 3], 'b': [10, 20, 30]})
        result = _extract_column(df, '1', 'y')
        assert result == [10, 20, 30]

    def test_extract_column_not_found(self):
        """Test extracting non-existent column."""
        df = pd.DataFrame({'a': [1, 2, 3]})
        with pytest.raises(Exception):
            _extract_column(df, 'nonexistent', 'y')

    def test_load_xy_from_file_csv(self, tmp_path):
        """Test loading X/Y from file (CSV)."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("x,y\n1,2\n2,4\n3,6\n")
        result = _load_xy_from_file(str(csv_file), 'x', 'y')
        assert 'x' in result
        assert 'y' in result

    def test_load_xy_from_file_excel(self, tmp_path):
        """Test loading X/Y from file (Excel)."""
        df = pd.DataFrame({'x': [1, 2, 3], 'y': [10, 20, 30]})
        excel_file = tmp_path / "test.xlsx"
        df.to_excel(excel_file, index=False)
        result = _load_xy_from_file(str(excel_file), 'x', 'y')
        assert 'x' in result
        assert 'y' in result

    def test_load_xy_from_file_text(self, tmp_path):
        """Test loading X/Y from file (text)."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("1 2\n3 4\n5 6\n")
        result = _load_xy_from_file(str(txt_file), None, None)
        assert 'x' in result
        assert 'y' in result


class TestCorrelationExtended:
    """Test correlation command extended scenarios."""

    def test_correlation_from_text(self, runner, tmp_path):
        """Test correlation from text file."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("1 2\n3 4\n5 6\n7 8\n9 10\n")
        result = runner.invoke(main, ['correlation', '-f', str(txt_file)])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'correlation' in data

    def test_correlation_no_data(self, runner):
        """Test correlation with no data."""
        result = runner.invoke(main, ['correlation'])
        assert result.exit_code != 0


class TestRegressionExtended:
    """Test regression command extended scenarios."""

    def test_regression_from_csv(self, runner, tmp_path):
        """Test regression from CSV file."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("x,y\n1,2\n2,4\n3,6\n4,8\n5,10\n")
        result = runner.invoke(main, ['regression', '-f', str(csv_file)])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'regression_type' in data

    def test_regression_no_data(self, runner):
        """Test regression with no data."""
        result = runner.invoke(main, ['regression'])
        assert result.exit_code != 0

    def test_regression_missing_columns(self, runner, tmp_path):
        """Test regression with missing columns."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("a,b\n1,2\n3,4\n")
        result = runner.invoke(main, [
            'regression', '-f', str(csv_file),
            '--x-column', 'nonexistent', '--y-column', 'b'
        ])
        assert result.exit_code != 0


class TestMultipleRegressionExtended:
    """Test multiple regression scenarios."""

    def test_multiple_regression_auto_columns(self, runner, tmp_path):
        """Test multiple regression with auto-detected columns."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("y,x1,x2\n10,1,2\n20,2,4\n30,3,6\n40,4,8\n50,5,10\n")
        result = runner.invoke(main, [
            'regression', '-f', str(csv_file),
            '--y-column', 'y', '--type', 'multiple'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['regression_type'] == 'multiple'


class TestStepwiseRegressionExtended:
    """Test stepwise regression scenarios."""

    def test_stepwise_forward(self, runner, tmp_path):
        """Test forward stepwise regression."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("y,x1,x2,x3\n10,1,2,3\n20,2,4,6\n30,3,6,9\n40,4,8,12\n50,5,10,15\n")
        result = runner.invoke(main, [
            'regression', '-f', str(csv_file),
            '--y-column', 'y', '--x-columns', 'x1', '--x-columns', 'x2', '--x-columns', 'x3',
            '--type', 'stepwise', '--direction', 'forward'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['regression_type'] == 'stepwise'

    def test_stepwise_backward(self, runner, tmp_path):
        """Test backward stepwise regression."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("y,x1,x2,x3\n10,1,2,3\n20,2,4,6\n30,3,6,9\n40,4,8,12\n50,5,10,15\n")
        result = runner.invoke(main, [
            'regression', '-f', str(csv_file),
            '--y-column', 'y', '--x-columns', 'x1', '--x-columns', 'x2', '--x-columns', 'x3',
            '--type', 'stepwise', '--direction', 'backward'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['regression_type'] == 'stepwise'
