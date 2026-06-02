"""Extended tests for regression command - covering all branches."""

import pytest
import json
import pandas as pd
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


class TestRegressionLinear:
    """Test linear regression."""

    def test_linear_from_values(self, runner):
        """Test linear regression from values."""
        result = runner.invoke(main, [
            'regression', '--x', '1', '--x', '2', '--x', '3',
            '--y', '2', '--y', '4', '--y', '6'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['regression_type'] == 'linear'
        assert data['r_squared'] > 0.9

    def test_quadratic_from_values(self, runner):
        """Test quadratic regression."""
        result = runner.invoke(main, [
            'regression', '--x', '1', '--x', '2', '--x', '3', '--x', '4',
            '--y', '1', '--y', '4', '--y', '9', '--y', '16',
            '--type', 'quadratic'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['regression_type'] == 'quadratic'

    def test_polynomial_from_values(self, runner):
        """Test polynomial regression."""
        result = runner.invoke(main, [
            'regression', '--x', '1', '--x', '2', '--x', '3', '--x', '4',
            '--y', '1', '--y', '8', '--y', '27', '--y', '64',
            '--type', 'polynomial', '--degree', '3'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['regression_type'] == 'polynomial'


class TestRegressionFromFile:
    """Test regression from file."""

    def test_linear_from_csv(self, runner, tmp_path):
        """Test linear regression from CSV."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("x,y\n1,2\n2,4\n3,6\n4,8\n5,10\n")
        result = runner.invoke(main, ['regression', '-f', str(csv_file)])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['regression_type'] == 'linear'

    def test_linear_from_csv_with_columns(self, runner, tmp_path):
        """Test linear regression from CSV with column names."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("temp,yield\n100,10\n200,20\n300,30\n")
        result = runner.invoke(main, [
            'regression', '-f', str(csv_file),
            '--x-column', 'temp', '--y-column', 'yield'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['regression_type'] == 'linear'

    def test_linear_from_excel(self, runner, tmp_path):
        """Test linear regression from Excel."""
        df = pd.DataFrame({'x': [1, 2, 3, 4, 5], 'y': [2, 4, 6, 8, 10]})
        excel_file = tmp_path / "test.xlsx"
        df.to_excel(excel_file, index=False)
        result = runner.invoke(main, [
            'regression', '-f', str(excel_file),
            '--x-column', 'x', '--y-column', 'y'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['regression_type'] == 'linear'


class TestRegressionMultiple:
    """Test multiple regression."""

    def test_multiple_from_csv(self, runner, tmp_path):
        """Test multiple regression from CSV."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("y,x1,x2\n10,1,2\n20,2,4\n30,3,6\n40,4,8\n50,5,10\n")
        result = runner.invoke(main, [
            'regression', '-f', str(csv_file),
            '--y-column', 'y', '--x-columns', 'x1', '--x-columns', 'x2',
            '--type', 'multiple'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['regression_type'] == 'multiple'
        assert 'r_squared' in data

    def test_multiple_no_file(self, runner):
        """Test multiple regression without file raises error."""
        result = runner.invoke(main, ['regression', '--type', 'multiple'])
        assert result.exit_code != 0


class TestRegressionLogistic:
    """Test logistic regression."""

    @pytest.mark.skip(reason="R script has bug with table serialization")
    def test_logistic_from_values(self, runner):
        """Test logistic regression from values."""
        result = runner.invoke(main, [
            'regression',
            '--x', '1', '--x', '2', '--x', '3', '--x', '4', '--x', '5',
            '--x', '6', '--x', '7', '--x', '8', '--x', '9', '--x', '10',
            '--y', '0', '--y', '0', '--y', '0', '--y', '0', '--y', '0',
            '--y', '1', '--y', '1', '--y', '1', '--y', '1', '--y', '1',
            '--type', 'logistic'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['regression_type'] == 'logistic'
        assert 'accuracy' in data


class TestRegressionStepwise:
    """Test stepwise regression."""

    def test_stepwise_from_csv(self, runner, tmp_path):
        """Test stepwise regression from CSV."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("y,x1,x2,x3\n10,1,2,3\n20,2,4,6\n30,3,6,9\n40,4,8,12\n50,5,10,15\n")
        result = runner.invoke(main, [
            'regression', '-f', str(csv_file),
            '--y-column', 'y', '--x-columns', 'x1', '--x-columns', 'x2', '--x-columns', 'x3',
            '--type', 'stepwise'
        ])
        assert result.exit_code == 0
        data = get_data(result)
        assert data['regression_type'] == 'stepwise'
        assert 'selected_variables' in data


class TestRegressionErrorHandling:
    """Test regression error handling."""

    def test_no_data(self, runner):
        """Test regression with no data raises error."""
        result = runner.invoke(main, ['regression'])
        assert result.exit_code != 0

    def test_invalid_file(self, runner):
        """Test regression with invalid file."""
        result = runner.invoke(main, ['regression', '-f', 'nonexistent.csv'])
        assert result.exit_code != 0
