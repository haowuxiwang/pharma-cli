"""Extended tests for normality command - covering interactive and report paths."""

import pytest
import json
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


class TestNormalityBasic:
    """Test basic normality functionality."""

    def test_normality_with_values(self, runner):
        """Test normality with direct values."""
        result = runner.invoke(main, [
            'normality', '-v', '10.2', '-v', '10.5', '-v', '10.1', '-v', '10.3', '-v', '10.4'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'shapiro_wilk' in data
        assert 'is_normal' in data

    def test_normality_with_csv(self, runner, tmp_path):
        """Test normality with CSV file."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("x\n10.2\n10.5\n10.1\n10.3\n10.4\n")
        result = runner.invoke(main, ['normality', '-f', str(csv_file)])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'is_normal' in data


class TestNormalityInteractive:
    """Test normality with interactive charts."""

    def test_normality_with_plot(self, runner):
        """Test normality with --plot flag."""
        result = runner.invoke(main, [
            '--plot', 'normality',
            '-v', '10.2', '-v', '10.5', '-v', '10.1', '-v', '10.3', '-v', '10.4'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'plot' in data

    def test_normality_with_interactive(self, runner):
        """Test normality with --interactive flag."""
        result = runner.invoke(main, [
            '--interactive', 'normality',
            '-v', '10.2', '-v', '10.5', '-v', '10.1', '-v', '10.3', '-v', '10.4'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'interactive_charts' in data


class TestNormalityReport:
    """Test normality with report generation."""

    def test_normality_with_report(self, runner):
        """Test normality with --report flag."""
        result = runner.invoke(main, [
            '--report', 'normality',
            '-v', '10.2', '-v', '10.5', '-v', '10.1', '-v', '10.3', '-v', '10.4'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert 'report_file' in data
