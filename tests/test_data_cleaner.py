"""Tests for cli/data_cleaner.py - dirty data handling."""
import pytest
import math
import tempfile
import os

from cli.data_cleaner import clean_values, detect_encoding, detect_delimiter, CleaningReport


class TestCleanValues:
    """Test clean_values function."""

    def test_clean_values_basic(self):
        """Test basic cleaning with valid data."""
        cleaned, report = clean_values([1.0, 2.0, 3.0])
        assert cleaned == [1.0, 2.0, 3.0]
        assert report.cleaned_count == 3
        assert report.removed_total == 0

    def test_clean_values_removes_none(self):
        """Test that None values are removed."""
        cleaned, report = clean_values([1.0, None, 3.0])
        assert cleaned == [1.0, 3.0]
        assert report.removed_nan == 1

    def test_clean_values_removes_nan(self):
        """Test that NaN values are removed."""
        cleaned, report = clean_values([1.0, float('nan'), 3.0])
        assert cleaned == [1.0, 3.0]
        assert report.removed_nan == 1

    def test_clean_values_removes_inf(self):
        """Test that Inf values are removed."""
        cleaned, report = clean_values([1.0, float('inf'), float('-inf'), 3.0])
        assert cleaned == [1.0, 3.0]
        assert report.removed_inf == 2

    def test_clean_values_removes_non_numeric(self):
        """Test that non-numeric values are removed."""
        cleaned, report = clean_values([1.0, "abc", 3.0])
        assert cleaned == [1.0, 3.0]
        assert report.removed_non_numeric == 1

    def test_clean_values_string_numbers(self):
        """Test that string numbers are converted."""
        cleaned, report = clean_values(["1.0", "2.0", "3.0"])
        assert cleaned == [1.0, 2.0, 3.0]
        assert report.cleaned_count == 3

    def test_clean_values_mixed_dirty(self):
        """Test cleaning with multiple types of dirty data."""
        data = [1.0, None, "abc", float('nan'), 2.0, float('inf'), 3.0]
        cleaned, report = clean_values(data)
        assert cleaned == [1.0, 2.0, 3.0]
        assert report.removed_nan == 2
        assert report.removed_inf == 1
        assert report.removed_non_numeric == 1

    def test_clean_values_empty_list(self):
        """Test cleaning empty list raises error."""
        with pytest.raises(ValueError, match="at least 1"):
            clean_values([])

    def test_clean_values_all_dirty(self):
        """Test cleaning when all values are dirty."""
        with pytest.raises(ValueError, match="at least 1"):
            clean_values([None, "abc", float('nan'), float('inf')])

    def test_clean_values_min_count(self):
        """Test min_count parameter."""
        cleaned, report = clean_values([1.0, 2.0], min_count=2)
        assert cleaned == [1.0, 2.0]

        with pytest.raises(ValueError, match="at least 3"):
            clean_values([1.0, 2.0], min_count=3)

    def test_clean_values_warnings(self):
        """Test that warnings are generated for removed values."""
        data = [1.0, "abc", float('inf')]
        cleaned, report = clean_values(data)
        assert len(report.warnings) >= 2  # non-numeric and inf warnings

    def test_clean_values_has_changes(self):
        """Test has_changes method."""
        # No changes
        report = CleaningReport()
        report.original_count = 3
        report.cleaned_count = 3
        assert not report.has_changes()

        # Has changes (removed_total = original - cleaned = 4 - 3 = 1)
        report2 = CleaningReport()
        report2.original_count = 4
        report2.cleaned_count = 3
        report2.removed_nan = 1
        assert report2.has_changes()

        # Has changes via warnings
        report3 = CleaningReport()
        report3.original_count = 3
        report3.cleaned_count = 3
        report3.warnings = ["some warning"]
        assert report3.has_changes()


class TestDetectEncoding:
    """Test detect_encoding function."""

    def test_detect_utf8(self, tmp_path):
        """Test detecting UTF-8 encoding."""
        file = tmp_path / "test.txt"
        file.write_text("hello world", encoding="utf-8")
        encoding = detect_encoding(str(file))
        assert encoding in ["utf-8-sig", "utf-8", "ascii"]

    def test_detect_gbk(self, tmp_path):
        """Test detecting GBK encoding."""
        file = tmp_path / "test.txt"
        file.write_text("你好世界", encoding="gbk")
        encoding = detect_encoding(str(file))
        assert encoding in ["gbk", "gb2312", "gb18030", "latin-1"]


class TestDetectDelimiter:
    """Test detect_delimiter function."""

    def test_detect_comma(self, tmp_path):
        """Test detecting comma delimiter."""
        file = tmp_path / "test.csv"
        file.write_text("a,b,c\n1,2,3\n4,5,6", encoding="utf-8")
        delimiter = detect_delimiter(str(file))
        assert delimiter == ","

    def test_detect_semicolon(self, tmp_path):
        """Test detecting semicolon delimiter."""
        file = tmp_path / "test.csv"
        file.write_text("a;b;c\n1;2;3\n4;5;6", encoding="utf-8")
        delimiter = detect_delimiter(str(file))
        assert delimiter == ";"

    def test_detect_tab(self, tmp_path):
        """Test detecting tab delimiter."""
        file = tmp_path / "test.tsv"
        file.write_text("a\tb\tc\n1\t2\t3\n4\t5\t6", encoding="utf-8")
        delimiter = detect_delimiter(str(file))
        assert delimiter == "\t"


class TestRealWorldDirtyData:
    """Test with real-world dirty data scenarios."""

    def test_csv_with_empty_cells(self):
        """Test CSV with empty cells (common real-world issue)."""
        # This simulates what happens when load_data processes CSV with empty cells
        data = [10.2, None, 10.5, None, 10.1]
        cleaned, report = clean_values(data)
        assert cleaned == [10.2, 10.5, 10.1]
        assert report.removed_nan == 2

    def test_excel_with_mixed_types(self):
        """Test Excel data with mixed types (numbers stored as strings)."""
        data = ["10.2", "10.5", "N/A", "10.1", ""]
        cleaned, report = clean_values(data, min_count=3)
        assert cleaned == [10.2, 10.5, 10.1]

    def test_data_with_header_row(self):
        """Test data where header row was accidentally included."""
        data = ["weight", 10.2, 10.5, 10.1]
        cleaned, report = clean_values(data, min_count=3)
        assert cleaned == [10.2, 10.5, 10.1]
        assert report.removed_non_numeric == 1

    def test_data_with_spaces(self):
        """Test data with whitespace around numbers."""
        data = [" 10.2 ", " 10.5", "10.1 "]
        # float() handles whitespace, so this should work
        cleaned, report = clean_values(data)
        assert len(cleaned) == 3
