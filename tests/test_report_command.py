"""Tests for report command and utils.py data loading."""

import pytest
import json
import os
from pathlib import Path
from click.testing import CliRunner
from cli.main import main
from cli.commands.utils import load_data, output, _load_excel, _load_csv, _load_json, _load_text, _extract_excel_column, _extract_csv_column


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


# ============================================================================
# Report Command Tests
# ============================================================================

class TestReportCommand:
    """Test report command."""

    def test_report_with_values(self, runner):
        """Test report with direct values."""
        result = runner.invoke(main, [
            'report', '-v', '10.2', '-v', '10.5', '-v', '10.1', '-v', '10.3', '-v', '10.4'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'report_file' in data
        assert 'analyses' in data

    def test_report_with_spec_limits(self, runner):
        """Test report with specification limits."""
        result = runner.invoke(main, [
            'report', '-v', '10.2', '-v', '10.5', '-v', '10.1', '-v', '10.3', '-v', '10.4',
            '--usl', '11.0', '--lsl', '9.0'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'analyses' in data
        assert 'capability' in data['analyses']

    def test_report_with_csv(self, runner, tmp_path):
        """Test report with CSV file."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("x\n10.2\n10.5\n10.1\n10.3\n10.4\n")
        result = runner.invoke(main, ['report', '-f', str(csv_file)])
        assert result.exit_code == 0


# ============================================================================
# Utils Data Loading Tests
# ============================================================================

class TestLoadData:
    """Test load_data function."""

    def test_load_data_from_values(self):
        """Test loading data from direct values."""
        result = load_data((10.2, 10.5, 10.1), None, None)
        assert 'values' in result
        assert len(result['values']) == 3

    def test_load_data_from_csv(self, tmp_path):
        """Test loading data from CSV file."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("x\n10.2\n10.5\n10.1\n")
        result = load_data(None, str(csv_file), None)
        assert 'values' in result
        assert len(result['values']) == 3

    def test_load_data_from_csv_with_column(self, tmp_path):
        """Test loading data from CSV with column selection."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("a,b\n1,10.2\n2,10.5\n3,10.1\n")
        result = load_data(None, str(csv_file), 'b')
        assert 'values' in result
        assert len(result['values']) == 3

    def test_load_data_from_json(self, tmp_path):
        """Test loading data from JSON file."""
        json_file = tmp_path / "test.json"
        json_file.write_text('{"values": [10.2, 10.5, 10.1]}')
        result = load_data(None, str(json_file), None)
        assert 'values' in result
        assert len(result['values']) == 3

    def test_load_data_from_text(self, tmp_path):
        """Test loading data from text file."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("10.2\n10.5\n10.1\n")
        result = load_data(None, str(txt_file), None)
        assert 'values' in result
        assert len(result['values']) == 3

    def test_load_data_empty_values(self):
        """Test loading empty values raises error."""
        with pytest.raises(Exception):
            load_data((), None, None)


class TestLoadExcel:
    """Test _load_excel function."""

    def test_load_excel_basic(self, tmp_path):
        """Test loading basic Excel file."""
        import pandas as pd
        excel_file = tmp_path / "test.xlsx"
        df = pd.DataFrame({'x': [10.2, 10.5, 10.1]})
        df.to_excel(excel_file, index=False)
        result = _load_excel(excel_file, None)
        assert 'values' in result

    def test_load_excel_with_column(self, tmp_path):
        """Test loading Excel with column selection."""
        import pandas as pd
        excel_file = tmp_path / "test.xlsx"
        df = pd.DataFrame({'a': [1, 2, 3], 'b': [10.2, 10.5, 10.1]})
        df.to_excel(excel_file, index=False)
        result = _load_excel(excel_file, 'b')
        assert 'values' in result
        assert len(result['values']) == 3

    def test_load_excel_with_sheet(self, tmp_path):
        """Test loading Excel with sheet selection."""
        import pandas as pd
        excel_file = tmp_path / "test.xlsx"
        with pd.ExcelWriter(excel_file) as writer:
            pd.DataFrame({'x': [10.2, 10.5]}).to_excel(writer, sheet_name='Sheet1', index=False)
            pd.DataFrame({'y': [20.1, 20.2]}).to_excel(writer, sheet_name='Sheet2', index=False)
        result = _load_excel(excel_file, None, 'Sheet2')
        assert 'values' in result


class TestLoadCsv:
    """Test _load_csv function."""

    def test_load_csv_basic(self, tmp_path):
        """Test loading basic CSV."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("x\n10.2\n10.5\n10.1\n")
        content = csv_file.read_text()
        result = _load_csv(csv_file, content, None)
        assert 'values' in result

    def test_load_csv_with_column(self, tmp_path):
        """Test loading CSV with column."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("a,b\n1,10.2\n2,10.5\n")
        content = csv_file.read_text()
        result = _load_csv(csv_file, content, 'b')
        assert 'values' in result

    def test_load_csv_semicolon_delimiter(self, tmp_path):
        """Test loading CSV with semicolon delimiter."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("a;b\n1;10.2\n2;10.5\n")
        content = csv_file.read_text()
        result = _load_csv(csv_file, content, None)
        assert 'values' in result


class TestLoadJson:
    """Test _load_json function."""

    def test_load_json_with_values(self):
        """Test loading JSON with values key."""
        content = '{"values": [10.2, 10.5, 10.1]}'
        result = _load_json(content)
        assert 'values' in result
        assert len(result['values']) == 3

    def test_load_json_without_values(self):
        """Test loading JSON without values key."""
        content = '{"x": 10.2, "y": 10.5}'
        result = _load_json(content)
        assert 'x' in result


class TestLoadText:
    """Test _load_text function."""

    def test_load_text_basic(self):
        """Test loading basic text."""
        content = "10.2\n10.5\n10.1\n"
        result = _load_text(content)
        assert 'values' in result
        assert len(result['values']) == 3

    def test_load_text_with_empty_lines(self):
        """Test loading text with empty lines."""
        content = "10.2\n\n10.5\n\n10.1\n"
        result = _load_text(content)
        assert 'values' in result
        assert len(result['values']) == 3

    def test_load_text_with_non_numeric(self):
        """Test loading text with non-numeric lines."""
        content = "header\n10.2\n10.5\n10.1\n"
        result = _load_text(content)
        assert 'values' in result
        assert len(result['values']) == 3


class TestOutput:
    """Test output function."""

    def test_output_success(self, capsys):
        """Test output with success data."""
        data = {"n": 5, "mean": 10.3}
        output(data)
        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result['status'] == 'success'
        assert result['data']['n'] == 5

    def test_output_error(self, capsys):
        """Test output with error data."""
        data = {"error": True, "message": "test error"}
        output(data)
        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result['status'] == 'error'
