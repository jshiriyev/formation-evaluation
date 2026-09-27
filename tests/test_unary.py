"""Tests for the first-significant-digit rounding helpers."""

import math

import numpy as np
import pytest

from pphys.onepage.wellview._unary import ceil, decimals, floor

# decimals


@pytest.mark.parametrize(
    ("x", "expected"),
    [
        (0.000532423, 4),
        (0.1, 1),
        (1.0, 0),
        (5.32, 0),
        (10.0, -1),
        (999.9, -2),
        (1312.0, -3),
        (-0.0532, 2),
        (np.float64(0.02), 2),
    ],
)
def test_decimals(x, expected):
    assert decimals(x) == expected


@pytest.mark.parametrize("x", [0.0, -0.0, math.nan, math.inf, -math.inf])
def test_decimals_of_zero_and_non_finite_values(x):
    assert decimals(x) == 0


# ceil and floor


@pytest.mark.parametrize(
    ("x", "down", "up"),
    [
        (0.000532423, 0.0005, 0.0006),
        (1312.0, 1000.0, 2000.0),
        (87.0, 80.0, 90.0),
        (-0.00532, -0.006, -0.005),
    ],
)
def test_first_significant_digit(x, down, up):
    assert floor(x) == down
    assert ceil(x) == up


@pytest.mark.parametrize(
    ("x", "ndigits", "down", "up"),
    [
        (3.14159, 2, 3.14, 3.15),
        (1312.0, -2, 1300.0, 1400.0),
        (0.000532423, -2, 0.0, 100.0),
        (1312.0, np.int64(-2), 1300.0, 1400.0),  # negative numpy integers
    ],
)
def test_given_decimal_places(x, ndigits, down, up):
    assert floor(x, ndigits) == down
    assert ceil(x, ndigits) == up


@pytest.mark.parametrize(
    ("x", "ndigits"), [(0.29, 2), (0.57, 2), (1.1, 2), (4.35, 2), (0.7, None)]
)
def test_values_on_the_step_are_kept(x, ndigits):
    # e.g. 0.29 * 100 is 28.999999999999996, which floored to 0.28
    assert floor(x, ndigits) == x
    assert ceil(x, ndigits) == x


def test_zero_and_non_finite_values_pass_through():
    assert floor(0.0) == ceil(0.0) == 0.0
    assert math.isnan(ceil(math.nan))
    assert floor(math.inf) == math.inf


def test_results_are_floats():
    assert all(isinstance(value, float) for value in (ceil(1312), floor(7, -1)))
