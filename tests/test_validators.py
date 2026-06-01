"""Tests for cli/validators.py."""

import pytest
import click
from cli.validators import (
    validate_values,
    validate_spec_limits,
    validate_groups,
    validate_xy,
    validate_alpha,
    validate_subgroup_size,
)


class TestValidateValues:
    """Tests for validate_values function."""

    def test_valid_values(self):
        """Test with valid values."""
        result = validate_values((1.0, 2.0, 3.0), min_count=1, name="values")
        assert result == [1.0, 2.0, 3.0]

    def test_single_value(self):
        """Test with single value."""
        result = validate_values((1.0,), min_count=1, name="values")
        assert result == [1.0]

    def test_empty_tuple(self):
        """Test with empty tuple."""
        with pytest.raises(click.UsageError, match="At least 1 values required"):
            validate_values((), min_count=1, name="values")

    def test_insufficient_values(self):
        """Test with insufficient values."""
        with pytest.raises(click.UsageError, match="At least 3 values required"):
            validate_values((1.0, 2.0), min_count=3, name="values")

    def test_nan_value(self):
        """Test with NaN value."""
        with pytest.raises(click.UsageError, match="NaN value at position 2"):
            validate_values((1.0, float('nan'), 3.0), min_count=1, name="values")

    def test_inf_value(self):
        """Test with Inf value."""
        with pytest.raises(click.UsageError, match="Inf value at position 2"):
            validate_values((1.0, float('inf'), 3.0), min_count=1, name="values")

    def test_negative_inf_value(self):
        """Test with negative Inf value."""
        with pytest.raises(click.UsageError, match="Inf value at position 2"):
            validate_values((1.0, float('-inf'), 3.0), min_count=1, name="values")


class TestValidateSpecLimits:
    """Tests for validate_spec_limits function."""

    def test_both_limits(self):
        """Test with both USL and LSL."""
        usl, lsl = validate_spec_limits(11.0, 9.0)
        assert usl == 11.0
        assert lsl == 9.0

    def test_only_usl(self):
        """Test with only USL."""
        usl, lsl = validate_spec_limits(11.0, None)
        assert usl == 11.0
        assert lsl is None

    def test_only_lsl(self):
        """Test with only LSL."""
        usl, lsl = validate_spec_limits(None, 9.0)
        assert usl is None
        assert lsl == 9.0

    def test_no_limits(self):
        """Test with no limits."""
        with pytest.raises(click.UsageError, match="At least one of --usl or --lsl is required"):
            validate_spec_limits(None, None)

    def test_usl_less_than_lsl(self):
        """Test with USL less than LSL."""
        with pytest.raises(click.UsageError, match="USL .* must be greater than LSL"):
            validate_spec_limits(9.0, 11.0)

    def test_usl_equal_to_lsl(self):
        """Test with USL equal to LSL."""
        with pytest.raises(click.UsageError, match="USL .* must be greater than LSL"):
            validate_spec_limits(10.0, 10.0)


class TestValidateGroups:
    """Tests for validate_groups function."""

    def test_valid_groups(self):
        """Test with valid groups."""
        groups = ('[1,2,3]', '[4,5,6]')
        result = validate_groups(groups, min_count=2)
        assert result == [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]

    def test_three_groups(self):
        """Test with three groups."""
        groups = ('[1,2,3]', '[4,5,6]', '[7,8,9]')
        result = validate_groups(groups, min_count=2)
        assert result == [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]]

    def test_insufficient_groups(self):
        """Test with insufficient groups."""
        groups = ('[1,2,3]',)
        with pytest.raises(click.UsageError, match="At least 2 groups required"):
            validate_groups(groups, min_count=2)

    def test_invalid_json(self):
        """Test with invalid JSON."""
        groups = ('[1,2,3]', 'invalid')
        with pytest.raises(click.UsageError, match="Invalid JSON in group 2"):
            validate_groups(groups, min_count=2)

    def test_not_array(self):
        """Test with non-array JSON."""
        groups = ('[1,2,3]', '{"key": "value"}')
        with pytest.raises(click.UsageError, match="Group 2 must be a JSON array"):
            validate_groups(groups, min_count=2)

    def test_insufficient_values_in_group(self):
        """Test with insufficient values in group."""
        groups = ('[1]', '[4,5,6]')
        with pytest.raises(click.UsageError, match="Group 1 must have at least 2 values"):
            validate_groups(groups, min_count=2)


class TestValidateXY:
    """Tests for validate_xy function."""

    def test_valid_xy(self):
        """Test with valid x and y."""
        x = (1.0, 2.0, 3.0)
        y = (2.0, 4.0, 6.0)
        x_list, y_list = validate_xy(x, y)
        assert x_list == [1.0, 2.0, 3.0]
        assert y_list == [2.0, 4.0, 6.0]

    def test_empty_x(self):
        """Test with empty x."""
        with pytest.raises(click.UsageError, match="Both --x and --y are required"):
            validate_xy((), (2.0, 4.0, 6.0))

    def test_empty_y(self):
        """Test with empty y."""
        with pytest.raises(click.UsageError, match="Both --x and --y are required"):
            validate_xy((1.0, 2.0, 3.0), ())

    def test_different_lengths(self):
        """Test with different lengths."""
        with pytest.raises(click.UsageError, match="--x and --y must have same length"):
            validate_xy((1.0, 2.0), (2.0, 4.0, 6.0))

    def test_insufficient_data_points(self):
        """Test with insufficient data points."""
        with pytest.raises(click.UsageError, match="At least 2 data points required"):
            validate_xy((1.0,), (2.0,))


class TestValidateAlpha:
    """Tests for validate_alpha function."""

    def test_valid_alpha(self):
        """Test with valid alpha."""
        result = validate_alpha(0.05)
        assert result == 0.05

    def test_alpha_near_zero(self):
        """Test with alpha near zero."""
        result = validate_alpha(0.001)
        assert result == 0.001

    def test_alpha_near_one(self):
        """Test with alpha near one."""
        result = validate_alpha(0.999)
        assert result == 0.999

    def test_alpha_zero(self):
        """Test with alpha zero."""
        with pytest.raises(click.UsageError, match="Alpha must be between 0 and 1"):
            validate_alpha(0.0)

    def test_alpha_one(self):
        """Test with alpha one."""
        with pytest.raises(click.UsageError, match="Alpha must be between 0 and 1"):
            validate_alpha(1.0)

    def test_alpha_negative(self):
        """Test with negative alpha."""
        with pytest.raises(click.UsageError, match="Alpha must be between 0 and 1"):
            validate_alpha(-0.05)

    def test_alpha_greater_than_one(self):
        """Test with alpha greater than one."""
        with pytest.raises(click.UsageError, match="Alpha must be between 0 and 1"):
            validate_alpha(1.5)


class TestValidateSubgroupSize:
    """Tests for validate_subgroup_size function."""

    def test_valid_size(self):
        """Test with valid size."""
        result = validate_subgroup_size(5)
        assert result == 5

    def test_minimum_size(self):
        """Test with minimum size."""
        result = validate_subgroup_size(2)
        assert result == 2

    def test_size_less_than_two(self):
        """Test with size less than two."""
        with pytest.raises(click.UsageError, match="Subgroup size must be at least 2"):
            validate_subgroup_size(1)

    def test_size_zero(self):
        """Test with size zero."""
        with pytest.raises(click.UsageError, match="Subgroup size must be at least 2"):
            validate_subgroup_size(0)

    def test_size_negative(self):
        """Test with negative size."""
        with pytest.raises(click.UsageError, match="Subgroup size must be at least 2"):
            validate_subgroup_size(-1)
