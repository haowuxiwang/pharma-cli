"""Tests for cli/r_engine.py."""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from cli.r_engine import find_rscript, run_r_script, run_r_file


class TestFindRscript:
    """Tests for find_rscript function."""

    @patch.dict(os.environ, {"RSCRIPT_PATH": "/path/to/Rscript"})
    @patch("os.path.isfile")
    def test_env_var_set(self, mock_isfile):
        """Test when RSCRIPT_PATH environment variable is set."""
        mock_isfile.return_value = True
        result = find_rscript()
        assert result == "/path/to/Rscript"
        mock_isfile.assert_called_once_with("/path/to/Rscript")

    @patch.dict(os.environ, {"RSCRIPT_PATH": ""}, clear=False)
    @patch("os.path.isfile")
    @patch("shutil.which")
    def test_env_var_empty(self, mock_which, mock_isfile):
        """Test when RSCRIPT_PATH environment variable is empty."""
        mock_isfile.return_value = False
        mock_which.return_value = "/usr/bin/Rscript"
        result = find_rscript()
        assert result == "/usr/bin/Rscript"

    @patch.dict(os.environ, {}, clear=True)
    @patch("os.path.isfile")
    @patch("shutil.which")
    def test_r_in_path(self, mock_which, mock_isfile):
        """Test when R is in PATH."""
        mock_isfile.return_value = False
        mock_which.return_value = "/usr/bin/Rscript"
        result = find_rscript()
        assert result == "/usr/bin/Rscript"

    @patch.dict(os.environ, {}, clear=True)
    @patch("os.path.isfile")
    @patch("shutil.which")
    def test_r_not_found(self, mock_which, mock_isfile):
        """Test when R is not found."""
        mock_isfile.return_value = False
        mock_which.return_value = None
        with pytest.raises(RuntimeError, match="Rscript not found"):
            find_rscript()

    @patch.dict(os.environ, {"RSCRIPT_PATH": "/nonexistent/path"})
    @patch("os.path.isfile")
    @patch("shutil.which")
    def test_env_var_nonexistent(self, mock_which, mock_isfile):
        """Test when RSCRIPT_PATH points to nonexistent file."""
        mock_isfile.return_value = False
        mock_which.return_value = "/usr/bin/Rscript"
        result = find_rscript()
        assert result == "/usr/bin/Rscript"


class TestRunRScript:
    """Tests for run_r_script function."""

    @patch("cli.r_engine.find_rscript")
    @patch("subprocess.run")
    def test_successful_execution(self, mock_run, mock_find_rscript):
        """Test successful R script execution."""
        mock_find_rscript.return_value = "/usr/bin/Rscript"
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"test": "success"}',
            stderr=""
        )
        result = run_r_script('cat(\'{"test": "success"}\')')
        assert result == {"test": "success"}

    @patch("cli.r_engine.find_rscript")
    @patch("subprocess.run")
    def test_execution_with_data(self, mock_run, mock_find_rscript):
        """Test R script execution with data."""
        mock_find_rscript.return_value = "/usr/bin/Rscript"
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"result": 42}',
            stderr=""
        )
        data = {"values": [1, 2, 3]}
        result = run_r_script('cat(\'{"result": 42}\')', data=data)
        assert result == {"result": 42}

    @patch("cli.r_engine.find_rscript")
    @patch("subprocess.run")
    def test_execution_error(self, mock_run, mock_find_rscript):
        """Test R script execution with error returns error dict."""
        mock_find_rscript.return_value = "/usr/bin/Rscript"
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Error in script"
        )
        result = run_r_script('stop("Error in script")')
        assert result["error"] is True
        assert result["error_type"] == "R_SCRIPT_ERROR"
        assert "Error in script" in result["message"]

    @patch("cli.r_engine.find_rscript")
    @patch("subprocess.run")
    def test_no_output(self, mock_run, mock_find_rscript):
        """Test R script execution with no output returns error dict."""
        mock_find_rscript.return_value = "/usr/bin/Rscript"
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="",
            stderr=""
        )
        result = run_r_script('')
        assert result["error"] is True
        assert result["error_type"] == "NO_OUTPUT"

    @patch("cli.r_engine.find_rscript")
    @patch("subprocess.run")
    def test_timeout(self, mock_run, mock_find_rscript):
        """Test R script execution timeout returns error dict."""
        import subprocess
        mock_find_rscript.return_value = "/usr/bin/Rscript"
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="Rscript", timeout=60)
        result = run_r_script('Sys.sleep(120)', timeout=60)
        assert result["error"] is True
        assert result["error_type"] == "TIMEOUT"


class TestRunRFile:
    """Tests for run_r_file function."""

    @patch("cli.r_engine.find_rscript")
    @patch("subprocess.run")
    def test_successful_execution(self, mock_run, mock_find_rscript, mock_r_script):
        """Test successful R file execution."""
        mock_find_rscript.return_value = "/usr/bin/Rscript"
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"test": "success"}',
            stderr=""
        )
        result = run_r_file(mock_r_script)
        assert result == {"test": "success"}

    @patch("cli.r_engine.find_rscript")
    def test_file_not_found(self, mock_find_rscript):
        """Test R file not found returns error dict."""
        mock_find_rscript.return_value = "/usr/bin/Rscript"
        result = run_r_file("/nonexistent/path/script.R")
        assert result["error"] is True
        assert result["error_type"] == "SCRIPT_NOT_FOUND"

    @patch("cli.r_engine.find_rscript")
    @patch("subprocess.run")
    def test_execution_error(self, mock_run, mock_find_rscript, mock_r_script_error):
        """Test R file execution with error returns error dict."""
        mock_find_rscript.return_value = "/usr/bin/Rscript"
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Error in script"
        )
        result = run_r_file(mock_r_script_error)
        assert result["error"] is True
        assert result["error_type"] == "R_SCRIPT_ERROR"

    @patch("cli.r_engine.find_rscript")
    @patch("subprocess.run")
    def test_execution_with_data(self, mock_run, mock_find_rscript, mock_r_script):
        """Test R file execution with data."""
        mock_find_rscript.return_value = "/usr/bin/Rscript"
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"result": 42}',
            stderr=""
        )
        data = {"values": [1, 2, 3]}
        result = run_r_file(mock_r_script, data=data)
        assert result == {"result": 42}

    @patch("cli.r_engine.find_rscript")
    @patch("subprocess.run")
    def test_custom_timeout(self, mock_run, mock_find_rscript, mock_r_script):
        """Test R file execution with custom timeout."""
        mock_find_rscript.return_value = "/usr/bin/Rscript"
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"test": "success"}',
            stderr=""
        )
        result = run_r_file(mock_r_script, timeout=30)
        assert result == {"test": "success"}
