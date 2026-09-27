"""Tests for :class:`pphys.Temperature`."""

import dataclasses

import numpy as np
import pytest

from pphys import Temperature

FT_TO_M = 0.3048


# Construction and defaults


@pytest.mark.parametrize(
    ("unit_system", "surface", "gradient"),
    [("field", 68.0, 0.024 * 1.8 * FT_TO_M), ("metric", 20.0, 0.024)],
)
def test_defaults(unit_system, surface, gradient):
    temp = Temperature(unit_system)

    assert temp.surface == surface
    assert temp.gradient == pytest.approx(gradient)
    assert temp.surface_depth == 0.0


def test_default_unit_system_is_field():
    assert Temperature().unit_system == "field"


def test_field_and_metric_defaults_agree():
    depths_m = np.array([0.0, 1000.0, 3000.0])

    metric = Temperature("metric")(depths_m)
    field = Temperature("field")(depths_m / FT_TO_M)

    np.testing.assert_allclose(Temperature.f_to_c(field), metric)


def test_custom_values_are_kept():
    temp = Temperature("metric", surface=4.0, gradient=0.03, surface_depth=500.0)

    assert (temp.surface, temp.gradient, temp.surface_depth) == (4.0, 0.03, 500.0)


@pytest.mark.parametrize("unit_system", ["international", "si", None])
def test_unknown_unit_system_raises(unit_system):
    with pytest.raises(ValueError, match="unit_system"):
        Temperature(unit_system)


def test_is_immutable():
    # Changing unit_system alone would leave surface and gradient in the old
    # units, so the model is frozen; use dataclasses.replace for variants.
    with pytest.raises(dataclasses.FrozenInstanceError):
        Temperature().unit_system = "metric"


# Evaluating temperatures


def test_linear_from_surface_depth():
    temp = Temperature("metric", surface=4.0, gradient=0.03, surface_depth=500.0)

    np.testing.assert_allclose(temp([500.0, 1500.0, 2500.0]), [4.0, 34.0, 64.0])


def test_scalar_depth():
    temp = Temperature("field", surface=70.0, gradient=0.015)

    assert temp(1000.0) == pytest.approx(85.0)


@pytest.mark.parametrize("unit", ["ft", "FT", "feet", "foot", "F"])
def test_feet_on_metric_model(unit):
    temp = Temperature("metric")

    np.testing.assert_allclose(temp(1000.0 / FT_TO_M, depth_unit=unit), temp(1000.0))


@pytest.mark.parametrize("unit", ["m", "M", "meter", "metres"])
def test_metres_on_field_model(unit):
    temp = Temperature("field")

    np.testing.assert_allclose(temp(1000.0 * FT_TO_M, depth_unit=unit), temp(1000.0))


def test_depth_unit_of_same_system_is_not_converted():
    temp = Temperature("field")

    np.testing.assert_allclose(temp([1000.0], depth_unit="ft"), temp([1000.0]))


def test_depth_unit_leaves_surface_depth_alone():
    # surface_depth is always in the model's own unit.
    temp = Temperature("metric", surface=4.0, gradient=0.03, surface_depth=500.0)

    assert temp(500.0 / FT_TO_M, depth_unit="ft") == pytest.approx(4.0)


def test_unknown_depth_unit_raises():
    with pytest.raises(ValueError, match="depth unit"):
        Temperature()([1000.0], depth_unit="km")


# Gradient and construction from two points


def test_get_gradient():
    assert Temperature.get_gradient(1000.0, 30.0, 2000.0, 55.0) == pytest.approx(0.025)
    assert Temperature.get_gradient(2000.0, 55.0, 1000.0, 30.0) == pytest.approx(0.025)


def test_get_gradient_equal_depths_raise():
    with pytest.raises(ValueError, match="differ"):
        Temperature.get_gradient(1000.0, 30.0, 1000.0, 35.0)


def test_from_points_reproduces_both_points():
    temp = Temperature.from_points(1000.0, 30.0, 2000.0, 55.0, unit_system="metric")

    assert temp.unit_system == "metric"
    assert temp.gradient == pytest.approx(0.025)
    assert temp.surface == pytest.approx(5.0)
    np.testing.assert_allclose(temp([1000.0, 2000.0]), [30.0, 55.0])


def test_from_points_with_surface_depth():
    temp = Temperature.from_points(
        1000.0, 30.0, 2000.0, 55.0, unit_system="metric", surface_depth=200.0
    )

    assert temp.surface == pytest.approx(10.0)
    np.testing.assert_allclose(temp([1000.0, 2000.0]), [30.0, 55.0])


def test_from_points_defaults_to_field():
    temp = Temperature.from_points(3000.0, 110.0, 6000.0, 150.0)

    assert temp.unit_system == "field"
    np.testing.assert_allclose(temp([3000.0, 6000.0]), [110.0, 150.0])


def test_from_points_equal_depths_raise():
    with pytest.raises(ValueError, match="differ"):
        Temperature.from_points(1000.0, 30.0, 1000.0, 35.0)


# Unit conversions and corrections


@pytest.mark.parametrize(
    ("fahrenheit", "celsius"), [(32.0, 0.0), (212.0, 100.0), (-40.0, -40.0)]
)
def test_temperature_conversions(fahrenheit, celsius):
    assert Temperature.f_to_c(fahrenheit) == pytest.approx(celsius)
    assert Temperature.c_to_f(celsius) == pytest.approx(fahrenheit)


def test_conversions_accept_lists():
    np.testing.assert_allclose(Temperature.c_to_f([0, 100]), [32.0, 212.0])


def test_resistivity_arps():
    expected = 0.1 * (75.0 + 6.77) / (150.0 + 6.77)

    assert Temperature.resistivity(0.1, 75.0, 150.0) == pytest.approx(expected)


def test_resistivity_round_trip():
    hot = Temperature.resistivity(0.1, 75.0, 150.0)

    assert Temperature.resistivity(hot, 150.0, 75.0) == pytest.approx(0.1)


@pytest.mark.parametrize("unit", ["C", "c"])
def test_resistivity_celsius_matches_fahrenheit(unit):
    celsius = Temperature.resistivity(0.1, 25.0, 80.0, temp_unit=unit)
    fahrenheit = Temperature.resistivity(0.1, 77.0, 176.0, temp_unit="F")

    assert celsius == pytest.approx(fahrenheit)


def test_resistivity_unknown_unit_raises():
    with pytest.raises(ValueError, match="temp_unit"):
        Temperature.resistivity(0.1, 75.0, 150.0, temp_unit="K")


def test_horner_recovers_formation_temperature():
    cooling_time, formation, slope = 6.0, 250.0, 30.0
    delta_time = np.array([4.0, 8.0, 12.0, 16.0])
    temps = formation - slope * np.log10((cooling_time + delta_time) / delta_time)

    assert Temperature.horner(temps, delta_time, cooling_time) == pytest.approx(
        formation
    )


@pytest.mark.parametrize(
    ("temps", "delta_time", "cooling_time", "message"),
    [
        ([200.0], [4.0], 6.0, "two runs"),
        ([200.0, 210.0], [4.0], 6.0, "two runs"),  # lengths differ
        ([200.0, 210.0], [0.0, 8.0], 6.0, "positive"),
        ([200.0, 210.0], [4.0, 8.0], 0.0, "positive"),
    ],
)
def test_horner_invalid_input_raises(temps, delta_time, cooling_time, message):
    with pytest.raises(ValueError, match=message):
        Temperature.horner(temps, delta_time, cooling_time)
