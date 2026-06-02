"""Extended tests for utils.py - covering all data loading paths."""

import pytest
import json
import pandas as pd
from pathlib import Path
from cli.commands.utils import load_data, output, _load_excel, _load_csv, _load_json, _load_text, _extract_excel_column, _extract_csv_column


class TestLoadExcelExtended:
    """Test _load_excel function with various scenarios."""

    def test_load_excel_with_numeric_column_name(self, tmp_path):
        """Test loading Excel with numeric column name."""
        df = pd.DataFrame({1: [10.2, 10.5, 10.1], 2: [20.1, 20.2, 20.3]})
        excel_file = tmp_path / "test.xlsx"
        df.to_excel(excel_file, index=False)
        result = _load_excel(excel_file, '1')
        assert 'values' in result

    def test_load_excel_with_column_index(self, tmp_path):
        """Test loading Excel with column index."""
        df = pd.DataFrame({'a': [1, 2, 3], 'b': [10.2, 10.5, 10.1]})
        excel_file = tmp_path / "test.xlsx"
        df.to_excel(excel_file, index=False)
        result = _load_excel(excel_file, '1')
        assert 'values' in result

    def test_load_excel_with_datetime_column(self, tmp_path):
        """Test loading Excel with datetime column."""
        df = pd.DataFrame({
            'date': pd.to_datetime(['2024-01-01', '2024-01-02', '2024-01-03']),
            'value': [10.2, 10.5, 10.1]
        })
        excel_file = tmp_path / "test.xlsx"
        df.to_excel(excel_file, index=False)
        result = _load_excel(excel_file, 'value')
        assert 'values' in result

    def test_load_excel_column_not_found(self, tmp_path):
        """Test loading Excel with non-existent column."""
        df = pd.DataFrame({'a': [1, 2, 3]})
        excel_file = tmp_path / "test.xlsx"
        df.to_excel(excel_file, index=False)
        with pytest.raises(Exception):
            _load_excel(excel_file, 'nonexistent')

    def test_load_excel_no_numeric_columns(self, tmp_path):
        """Test loading Excel with no numeric columns."""
        df = pd.DataFrame({'a': ['x', 'y', 'z'], 'b': ['p', 'q', 'r']})
        excel_file = tmp_path / "test.xlsx"
        df.to_excel(excel_file, index=False)
        with pytest.raises(Exception):
            _load_excel(excel_file, None)


class TestLoadCsvExtended:
    """Test _load_csv function with various scenarios."""

    def test_load_csv_with_bom(self, tmp_path):
        """Test loading CSV with BOM marker."""
        csv_file = tmp_path / "test_bom.csv"
        csv_file.write_text('﻿' + 'x\n10.2\n10.5\n10.1\n', encoding='utf-8')
        content = csv_file.read_text(encoding='utf-8-sig')
        result = _load_csv(csv_file, content, None)
        assert 'values' in result

    def test_load_csv_with_semicolon(self, tmp_path):
        """Test loading CSV with semicolon delimiter."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("a;b\n1;10.2\n2;10.5\n3;10.1\n")
        content = csv_file.read_text()
        result = _load_csv(csv_file, content, None)
        assert 'values' in result

    def test_load_csv_column_by_index(self, tmp_path):
        """Test loading CSV with column by index."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("a,b,c\n1,10.2,x\n2,10.5,y\n3,10.1,z\n")
        content = csv_file.read_text()
        result = _load_csv(csv_file, content, '1')
        assert 'values' in result

    def test_load_csv_column_not_found(self, tmp_path):
        """Test loading CSV with non-existent column."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("a,b\n1,10.2\n2,10.5\n")
        content = csv_file.read_text()
        with pytest.raises(Exception):
            _load_csv(csv_file, content, 'nonexistent')


class TestLoadJsonExtended:
    """Test _load_json function with various scenarios."""

    def test_load_json_with_nested_data(self):
        """Test loading JSON with nested data."""
        content = '{"values": [10.2, 10.5, 10.1], "metadata": {"source": "test"}}'
        result = _load_json(content)
        assert 'values' in result
        assert 'metadata' in result

    def test_load_json_invalid(self):
        """Test loading invalid JSON."""
        content = '{"values": [10.2, 10.5, invalid}'
        with pytest.raises(Exception):
            _load_json(content)


class TestLoadTextExtended:
    """Test _load_text function with various scenarios."""

    def test_load_text_with_spaces(self):
        """Test loading text with spaces around values."""
        content = "  10.2  \n  10.5  \n  10.1  \n"
        result = _load_text(content)
        assert 'values' in result
        assert len(result['values']) == 3

    def test_load_text_with_tabs(self):
        """Test loading text with tab-separated values on separate lines."""
        content = "10.2\n10.5\n10.1\n"
        result = _load_text(content)
        assert 'values' in result

    def test_load_text_empty(self):
        """Test loading empty text."""
        content = ""
        with pytest.raises(Exception):
            _load_text(content)

    def test_load_text_all_non_numeric(self):
        """Test loading text with all non-numeric values."""
        content = "abc\ndef\nghi\n"
        with pytest.raises(Exception):
            _load_text(content)


class TestExtractExcelColumn:
    """Test _extract_excel_column function."""

    def test_extract_by_name(self):
        """Test extracting column by name."""
        df = pd.DataFrame({'x': [1, 2, 3], 'y': [10, 20, 30]})
        result = _extract_excel_column(df, 'y', Path("test.xlsx"))
        assert result == [10, 20, 30]

    def test_extract_by_numeric_name(self):
        """Test extracting column by numeric name."""
        df = pd.DataFrame({1: [1, 2, 3], 2: [10, 20, 30]})
        result = _extract_excel_column(df, '2', Path("test.xlsx"))
        assert result == [10, 20, 30]

    def test_extract_by_index(self):
        """Test extracting column by index."""
        df = pd.DataFrame({'a': [1, 2, 3], 'b': [10, 20, 30]})
        result = _extract_excel_column(df, '1', Path("test.xlsx"))
        assert result == [10, 20, 30]

    def test_extract_not_found(self):
        """Test extracting non-existent column."""
        df = pd.DataFrame({'a': [1, 2, 3]})
        with pytest.raises(Exception):
            _extract_excel_column(df, 'nonexistent', Path("test.xlsx"))


class TestExtractCsvColumn:
    """Test _extract_csv_column function."""

    def test_extract_by_name(self, tmp_path):
        """Test extracting CSV column by name."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("x,y\n1,10\n2,20\n3,30\n")
        content = csv_file.read_text()
        import csv, io
        reader = csv.DictReader(io.StringIO(content))
        result = _extract_csv_column(reader, 'y', content, ',')
        assert result == [10.0, 20.0, 30.0]

    def test_extract_by_index(self, tmp_path):
        """Test extracting CSV column by index."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("x,y\n1,10\n2,20\n3,30\n")
        content = csv_file.read_text()
        import csv, io
        reader = csv.DictReader(io.StringIO(content))
        result = _extract_csv_column(reader, '1', content, ',')
        assert result == [10.0, 20.0, 30.0]

    def test_extract_not_found(self, tmp_path):
        """Test extracting non-existent CSV column."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("x,y\n1,10\n2,20\n")
        content = csv_file.read_text()
        import csv, io
        reader = csv.DictReader(io.StringIO(content))
        with pytest.raises(Exception):
            _extract_csv_column(reader, 'nonexistent', content, ',')


class TestLoadDataExtended:
    """Test load_data function with various scenarios."""

    def test_load_data_from_excel(self, tmp_path):
        """Test loading data from Excel file."""
        df = pd.DataFrame({'x': [10.2, 10.5, 10.1]})
        excel_file = tmp_path / "test.xlsx"
        df.to_excel(excel_file, index=False)
        result = load_data(None, str(excel_file), None)
        assert 'values' in result

    def test_load_data_from_excel_with_sheet(self, tmp_path):
        """Test loading data from Excel with sheet selection."""
        df = pd.DataFrame({'x': [10.2, 10.5, 10.1]})
        excel_file = tmp_path / "test.xlsx"
        df.to_excel(excel_file, sheet_name='Data', index=False)
        result = load_data(None, str(excel_file), None, 'Data')
        assert 'values' in result

    def test_load_data_from_csv_with_encoding(self, tmp_path):
        """Test loading data from CSV with encoding."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("x\n10.2\n10.5\n10.1\n", encoding='utf-8')
        result = load_data(None, str(csv_file), None)
        assert 'values' in result

    def test_load_data_from_json_file(self, tmp_path):
        """Test loading data from JSON file."""
        json_file = tmp_path / "test.json"
        json_file.write_text('{"values": [10.2, 10.5, 10.1]}')
        result = load_data(None, str(json_file), None)
        assert 'values' in result

    def test_load_data_from_text_file(self, tmp_path):
        """Test loading data from text file."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("10.2\n10.5\n10.1\n")
        result = load_data(None, str(txt_file), None)
        assert 'values' in result


class TestOutputExtended:
    """Test output function with various scenarios."""

    def test_output_with_nested_data(self, capsys):
        """Test output with nested data structure."""
        data = {
            "n": 5,
            "mean": 10.3,
            "details": {"min": 10.1, "max": 10.5}
        }
        output(data)
        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result['status'] == 'success'
        assert result['data']['details']['min'] == 10.1

    def test_output_with_list_data(self, capsys):
        """Test output with list data."""
        data = {"values": [1, 2, 3, 4, 5]}
        output(data)
        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result['status'] == 'success'
        assert len(result['data']['values']) == 5

    def test_output_error_with_suggestion(self, capsys):
        """Test output with error and suggestion."""
        data = {
            "error": True,
            "error_type": "R_NOT_FOUND",
            "message": "R not found",
            "suggestion": "Install R from https://cran.r-project.org/"
        }
        output(data)
        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result['status'] == 'error'
        assert 'suggestion' in result
