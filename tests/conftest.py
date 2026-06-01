"""Shared fixtures for pharma-cli tests."""

import pytest
import tempfile
import os
from pathlib import Path


@pytest.fixture
def sample_values():
    """Sample numeric values for testing."""
    return [10.2, 10.5, 10.1, 10.3, 10.4]


@pytest.fixture
def sample_values_large():
    """Larger sample of numeric values for testing."""
    return [10.2, 10.5, 10.1, 10.3, 10.4, 10.6, 10.3, 10.5, 10.2, 10.4]


@pytest.fixture
def sample_csv_file(tmp_path):
    """Create a temporary CSV file for testing."""
    csv_content = "measurement\n10.2\n10.5\n10.1\n10.3\n10.4\n"
    csv_file = tmp_path / "test_data.csv"
    csv_file.write_text(csv_content)
    return str(csv_file)


@pytest.fixture
def sample_txt_file(tmp_path):
    """Create a temporary TXT file for testing."""
    txt_content = "10.2\n10.5\n10.1\n10.3\n10.4\n"
    txt_file = tmp_path / "test_data.txt"
    txt_file.write_text(txt_content)
    return str(txt_file)


@pytest.fixture
def sample_json_file(tmp_path):
    """Create a temporary JSON file for testing."""
    import json
    json_content = json.dumps({"values": [10.2, 10.5, 10.1, 10.3, 10.4]})
    json_file = tmp_path / "test_data.json"
    json_file.write_text(json_content)
    return str(json_file)


@pytest.fixture
def mock_r_script(tmp_path):
    """Create a mock R script for testing."""
    r_script = tmp_path / "test_script.R"
    r_script.write_text('cat(\'{"test": "success"}\')')
    return str(r_script)


@pytest.fixture
def mock_r_script_error(tmp_path):
    """Create a mock R script that raises an error."""
    r_script = tmp_path / "test_script_error.R"
    r_script.write_text('stop("Test error")')
    return str(r_script)
