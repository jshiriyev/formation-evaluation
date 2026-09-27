"""Curve families recognized from LAS mnemonics and units.

A family tells how a curve is displayed (linear or logarithmic axis, colour)
and which values are physically plausible, which :class:`pphys.LasView`
uses for quality control.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field

# Canonical unit -> spellings found in LAS files (compared upper-case, without
# spaces).
_UNIT_SPELLINGS = {
    "OHMM": ("OHMM", "OHM.M", "OHM-M", "OHM*M", "OHM_M"),
    "GAPI": ("GAPI", "API", "API-GR"),
    "G/CC": (
        "G/CC",
        "G/CM3",
        "G/C3",
        "GM/CC",
        "GR/CC",
        "GRAM/CC",
        "GRAMPERCC",
        "GMPERCC",
    ),
    "K/M3": ("K/M3", "KG/M3"),
    "US/F": ("US/F", "US/FT", "USEC/FT", "MUS/FT", "MU-SEC/FT", "MICROSEC/FT"),
    "US/M": ("US/M", "USEC/M"),
    "V/V": ("V/V", "DEC", "DECP", "FRAC", "FRACTION", "M3/M3", "CFCF"),
    "PU": ("PU", "P.U.", "LS-PU", "SS-PU", "DS-PU", "PU-L", "PU-S"),
    "%": ("%", "PCT", "PERCENT"),
    "IN": ("IN", "INCH", "INCHES"),
    "MM": ("MM",),
    "CM": ("CM",),
    "DEG": ("DEG", "DEGREE", "DEGREES", "°"),
    "MV": ("MV", "MILLIVOLTS"),
    "B/E": ("B/E", "BARN/E", "BARNS/E", "BARNS/ELECTRON"),
    "DB/F": ("DB/F", "DB/FT"),
    "DB/M": ("DB/M",),
    "PPM": ("PPM", "PARTS-PER-MIL", "PARTSPERMILLION"),
    "DEGC": ("DEGC", "°C", "DEG_C", "DEGC."),
    "DEGF": ("DEGF", "°F", "DEG_F", "DEGF."),
}
_CANONICAL_UNIT = {
    spelling: canonical
    for canonical, spellings in _UNIT_SPELLINGS.items()
    for spelling in spellings
}

ANY_UNIT = "*"


def normalize_unit(unit: str | None) -> str:
    """Return the canonical spelling of ``unit`` (e.g. "gm/cc" -> "G/CC")."""
    key = (unit or "").strip().upper().replace(" ", "")
    return _CANONICAL_UNIT.get(key, key)


@dataclass(frozen=True)
class CurveFamily:
    """A kind of log curve and how to display and check it.

    Parameters
    ----------
    name : str
        Family name, e.g. "gamma ray".
    pattern : str
        Regular expression that must fully match the mnemonic (upper-case,
        spaces removed).
    ranges : dict
        Physically plausible ``(min, max)`` per canonical unit. The key "*"
        applies to any unit.
    units : tuple of str
        Canonical units that identify the family when the mnemonic is not
        recognized, e.g. "OHMM" for resistivity.
    log_scale : bool
        Display on a logarithmic axis.
    color : str
        Default plot colour.
    smooth : bool
        Values change smoothly with depth, so spikes and long constant runs
        point to problems. False for spiky or wrapping curves such as the
        casing collar locator or azimuths.
    """

    name: str
    pattern: str
    ranges: dict[str, tuple[float, float]] = field(default_factory=dict)
    units: tuple[str, ...] = ()
    log_scale: bool = False
    color: str = "black"
    smooth: bool = True

    def matches(self, mnemonic: str) -> bool:
        """Return True if ``mnemonic`` belongs to this family."""
        return re.fullmatch(self.pattern, _normalize_mnemonic(mnemonic)) is not None

    def range_for(self, unit: str | None) -> tuple[float, float] | None:
        """Return the plausible ``(min, max)`` for ``unit``, if known."""
        return self.ranges.get(normalize_unit(unit), self.ranges.get(ANY_UNIT))


_INF = math.inf
_CALIPER_RANGES = {"IN": (3.0, 40.0), "MM": (75.0, 1000.0), "CM": (7.5, 100.0)}

# Order matters where patterns overlap: the first match wins.
FAMILIES: tuple[CurveFamily, ...] = (
    CurveFamily(
        "density correction",
        r"DRHO|DRH|DRHB|HDRA|ZCOR|DCOR|DENCORR?|DENSITYCORR",
        {"G/CC": (-0.5, 0.5), "K/M3": (-500.0, 500.0)},
        color="gray",
    ),
    CurveFamily(
        "bulk density",
        r"RHOB|RHOZ|RHO8|RHOM|ZDEN|HDEN|DEN|DENS|DENSITY|BDEL",
        {"G/CC": (1.0, 3.3), "K/M3": (1000.0, 3300.0)},
        units=("G/CC", "K/M3"),
        color="red",
    ),
    CurveFamily(
        "neutron porosity",
        r"NPHI[A-Z0-9_]*|TNPH|NPOR|NPHS|NPLS|NPSS|CNC|CNCF|CNL|CN|HNPO|APLC|PHIN"
        r"|NEU|NEUT|NEUTRON|NEUTRONPOROSITY",
        {"V/V": (-0.15, 1.0), "PU": (-15.0, 100.0), "%": (-15.0, 100.0)},
        color="blue",
    ),
    CurveFamily(
        "photoelectric factor",
        r"PEF|PE|PEFZ|PEFL|PEF8|PDPE|PEFS",
        {ANY_UNIT: (0.0, 10.0)},
        units=("B/E",),
        color="magenta",
    ),
    CurveFamily(
        "shear sonic",
        r"DTS[A-Z0-9_]*|DT4S|DTSH",
        {"US/F": (60.0, 800.0), "US/M": (200.0, 2600.0)},
        color="purple",
    ),
    CurveFamily(
        "sonic",
        r"DT[A-Z0-9_]*|AC|ACS|SONIC",
        {"US/F": (40.0, 250.0), "US/M": (130.0, 820.0)},
        units=("US/F", "US/M"),
        color="navy",
    ),
    CurveFamily(
        "caliper",
        r"CAL[A-Z0-9_]*|HCAL|LCAL|C1|C2|C3",
        _CALIPER_RANGES,
        color="saddlebrown",
    ),
    CurveFamily(
        "bit size",
        r"BS|BIT|BITSIZE|BSZ",
        _CALIPER_RANGES,
        color="gray",
    ),
    CurveFamily(
        "potassium",
        r"POTA|K|HFK|KPOT|POTASSIUM",
        {"%": (0.0, 10.0), "V/V": (0.0, 0.1)},
        color="darkgreen",
    ),
    CurveFamily(
        "thorium",
        r"THOR|TH|HTHO|THORIUM",
        {"PPM": (0.0, 100.0)},
        color="darkorange",
    ),
    CurveFamily(
        "uranium",
        r"URAN|U|HURA|URANIUM",
        {"PPM": (0.0, 100.0)},
        color="darkviolet",
    ),
    CurveFamily(
        "gamma ray",
        r"GR[A-Z0-9_]*|SGR|CGR|HSGR|HCGR|ECGR|EHGR|GAMMA[A-Z0-9_]*",
        {"GAPI": (0.0, 500.0)},
        units=("GAPI",),
        color="green",
    ),
    CurveFamily(
        "spontaneous potential",
        r"SP|SPC|SPBL|SPBR|SSP|PSP",
        {"MV": (-500.0, 500.0)},
        color="black",
    ),
    CurveFamily(
        "resistivity",
        r"RT|RD|RS|RM|RXO[A-Z0-9_]*|RLA[0-9]|MSFL|MLL|SFLU?|LLD|LLS|ILD|ILM|RILD|RILM"
        r"|RDEP|RMED|RSHAL|HLLD|HLLS|HDRS|HMRS|A[TOF][0-9]{2}[A-Z0-9_]*|AHT[0-9]{2}"
        r"|M2R[0-9X]|P[0-9]{2}H|RES[A-Z0-9_]*",
        {"OHMM": (0.01, 1e5)},
        units=("OHMM",),
        log_scale=True,
        color="black",
    ),
    CurveFamily(
        "attenuation",
        r"AT(AV|MN|MX|C[0-9]+)[A-Z0-9_]*|ATTN[A-Z0-9_]*",
        {"DB/F": (0.0, 50.0), "DB/M": (0.0, 165.0)},
        units=("DB/F", "DB/M"),
        color="olive",
    ),
    CurveFamily(
        "casing collar locator",
        r"CCL[A-Z0-9_]*|COLLAR",
        color="gray",
        smooth=False,
    ),
    CurveFamily(
        "deviation",
        r"DEV[A-Z0-9_]*|DEVI|INCL|INC|HDEV|DEVIATION",
        {"DEG": (0.0, 180.0)},
        color="black",
    ),
    CurveFamily(
        "azimuth",
        r"AZI[A-Z0-9_]*|HAZI|AZIM|P1AZ|HLAZ|RB[A-Z0-9_]*|RELBEAR[A-Z0-9_]*",
        {"DEG": (0.0, 360.0)},
        color="black",
        smooth=False,  # values wrap from 360 to 0
    ),
    CurveFamily(
        "tension",
        r"TENS|TTEN|HTEN|CHT|TEN[A-Z0-9_]*|TENSION",
        {ANY_UNIT: (0.0, _INF)},
        color="black",
    ),
    CurveFamily(
        "logging speed",
        r"SPD[A-Z0-9_]*|SPEED|CS|LSPD|CVEL",
        {ANY_UNIT: (0.0, _INF)},
        color="black",
    ),
    CurveFamily(
        "temperature",
        r"TEMP[A-Z0-9_]*|MTEM|MTEMP|BHT|HTEM",
        {"DEGC": (-40.0, 400.0), "DEGF": (-40.0, 750.0)},
        color="firebrick",
    ),
    CurveFamily(
        "volume fraction",
        r"PHI[A-Z0-9_]*|POR[A-Z0-9_]*|SW[A-Z0-9_]*|SXO|VSH[A-Z0-9_]*|VCL[A-Z0-9_]*|BVW",
        {"V/V": (0.0, 1.0), "PU": (0.0, 100.0), "%": (0.0, 100.0)},
        color="teal",
    ),
)


def classify(mnemonic: str, unit: str | None = None) -> CurveFamily | None:
    """Return the family of a curve, or None if it is not recognized.

    The mnemonic is tried first. If it matches no family, a unit that
    identifies one (e.g. "OHMM" for resistivity) is used instead.
    """
    for family in FAMILIES:
        if family.matches(mnemonic):
            return family

    canonical = normalize_unit(unit)
    if canonical:
        for family in FAMILIES:
            if canonical in family.units:
                return family

    return None


def _normalize_mnemonic(mnemonic: str) -> str:
    """Upper-case ``mnemonic`` and drop spaces ("Bit Size" -> "BITSIZE")."""
    return mnemonic.strip().upper().replace(" ", "")
