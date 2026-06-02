"""Extended tests for gage-rr command - covering all analysis types."""

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


class TestGageRrCrossed:
    """Test crossed Gage R&R."""

    def test_crossed_basic(self, runner):
        """Test basic crossed Gage R&R."""
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
            '-o', 'O1', '-o', 'O2', '-o', 'O3',
            '--tolerance', '2.0'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['analysis_type'] == 'crossed_gage_rr'
        assert 'variance_components' in data
        assert 'ndc' in data


class TestGageRrBias:
    """Test bias study."""

    def test_bias_basic(self, runner):
        """Test basic bias study."""
        result = runner.invoke(main, [
            'gage-rr', 'bias',
            '-m', '10.1', '-m', '10.2', '-m', '10.3', '-m', '10.0', '-m', '10.2',
            '--reference-value', '10.0'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['analysis_type'] == 'bias'
        assert 'bias' in data
        assert 'p_value' in data


class TestGageRrStability:
    """Test stability study."""

    def test_stability_basic(self, runner):
        """Test basic stability study."""
        result = runner.invoke(main, [
            'gage-rr', 'stability',
            '-m', '10.1', '-m', '10.2', '-m', '10.3', '-m', '10.4', '-m', '10.5'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['analysis_type'] == 'stability'
        assert 'out_of_control' in data

    def test_stability_with_limits(self, runner):
        """Test stability study with tolerance."""
        result = runner.invoke(main, [
            'gage-rr', 'stability',
            '-m', '10.1', '-m', '10.2', '-m', '10.3', '-m', '10.4', '-m', '10.5',
            '--tolerance', '2.0'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['analysis_type'] == 'stability'


class TestGageRrLinearity:
    """Test linearity study."""

    def test_linearity_basic(self, runner):
        """Test basic linearity study."""
        result = runner.invoke(main, [
            'gage-rr', 'linearity',
            '-m', '10.1', '-m', '10.2', '-m', '10.3', '-m', '10.4', '-m', '10.5',
            '--reference-values', '10.0', '--reference-values', '10.1',
            '--reference-values', '10.2', '--reference-values', '10.3',
            '--reference-values', '10.4'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['analysis_type'] == 'linearity'
        assert 'slope' in data


class TestGageRrAttribute:
    """Test attribute agreement analysis."""

    def test_attribute_requires_file(self, runner):
        """Test attribute analysis requires file."""
        result = runner.invoke(main, ['gage-rr', 'attribute'])
        assert result.exit_code != 0


class TestGageRrErrorHandling:
    """Test gage-rr error handling."""

    def test_crossed_missing_params(self, runner):
        """Test crossed with missing parameters."""
        result = runner.invoke(main, ['gage-rr', 'crossed'])
        assert result.exit_code != 0

    def test_bias_missing_reference(self, runner):
        """Test bias without reference value."""
        result = runner.invoke(main, [
            'gage-rr', 'bias',
            '-m', '10.1', '-m', '10.2', '-m', '10.3'
        ])
        assert result.exit_code != 0
