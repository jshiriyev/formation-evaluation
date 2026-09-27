"""Tests for the curve-family catalogue in :mod:`pphys._families`."""

import math

import pytest

from pphys._families import FAMILIES, classify, normalize_unit


@pytest.mark.parametrize(
    ("mnemonic", "unit", "family"),
    [
        ("GR", "GAPI", "gamma ray"),
        ("GammaTotal", "api", "gamma ray"),
        ("SP", "MV", "spontaneous potential"),
        ("SPD", "M/MN", "logging speed"),  # not SP
        ("AT90", "OHMM", "resistivity"),
        ("ATC1", "DB/F", "attenuation"),  # not AT90-style resistivity
        ("LLD", "Ohm-m", "resistivity"),
        ("DTS", "US/F", "shear sonic"),
        ("DTMN", "US/F", "sonic"),
        ("NPHI", "V/V", "neutron porosity"),
        ("PHIT", "V/V", "volume fraction"),
        ("RHOB", "G/CC", "bulk density"),
        ("DRHO", "G/CC", "density correction"),
        ("Bit Size", "inches", "bit size"),
        ("CALI", "IN", "caliper"),
        ("CCL", "MV", "casing collar locator"),
        ("RBSB", "DEG", "azimuth"),
        ("DEVOD", "DEG", "deviation"),
        ("TTEN", "LBF", "tension"),
        ("Thorium", "parts-per-mil", "thorium"),
    ],
)
def test_classify_by_mnemonic(mnemonic, unit, family):
    assert classify(mnemonic, unit).name == family


def test_classify_falls_back_to_unit():
    assert classify("XYZ", "ohm.m").name == "resistivity"
    assert classify("XYZ", "GAPI").name == "gamma ray"


def test_unknown_curve():
    assert classify("XYZ", "") is None
    assert classify("XYZ", None) is None


@pytest.mark.parametrize(
    ("unit", "canonical"),
    [
        ("gm/cc", "G/CC"),
        ("Ohm-m", "OHMM"),
        ("mu-sec/ft", "US/F"),
        ("ls-pu", "PU"),
        ("decp", "V/V"),
        (" in ", "IN"),
        ("furlong", "FURLONG"),  # unknown units are only upper-cased
        (None, ""),
    ],
)
def test_normalize_unit(unit, canonical):
    assert normalize_unit(unit) == canonical


def test_range_depends_on_unit():
    neutron = classify("NPHI")

    assert neutron.range_for("V/V") == (-0.15, 1.0)
    assert neutron.range_for("pu") == (-15.0, 100.0)
    assert neutron.range_for("furlong") is None


def test_any_unit_range():
    assert classify("TTEN").range_for("whatever") == (0.0, math.inf)


def test_family_names_are_unique():
    names = [family.name for family in FAMILIES]
    assert len(names) == len(set(names))
