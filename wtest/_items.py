from dataclasses import dataclass

@dataclass
class reservoir:
    """
    k       : permeability in mD
    phi     : porosity
    h       : formation thickness, ft
    cr      : rock compressibility, 1/psi
    """
    permeability: float = None
    porosity: float = None
    thickness: float = None
    compressibility: float = None

@dataclass
class well:
    """
    rate    : constant flow rate, STB/day
    time    : time array when to calculate bottom hole pressure, days
    rw      : wellbore radius, ft
    skin    : skin factor, dimensionless
    """
    rate: float = None
    pressure: float = None
    time: float = None
    radius: float = None
    skin: float = None

@dataclass
class fluid:
    """
    mu      : viscosity in cp
    cf      : fluid compressibility in 1/psi
    fvf     : formation volume factor, bbl/STB
    """
    viscosity: float = None
    density: float = None
    compressibility: float = None
    fvf: float = 1