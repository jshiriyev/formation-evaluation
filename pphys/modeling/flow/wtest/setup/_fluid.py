from dataclasses import dataclass

@dataclass
class Fluid:
    """
    visc    : phase viscosity, cp
    rho     : phase density, lb/ft3
    comp    : phase compressibility, 1/psi
    fvf     : phase formation volume factor, bbl/STB
    """
    visc    : float = None
    rho     : float = None
    comp    : float = None
    fvf     : float = 1.

    satur   : float = 1.
    rperm   : float = 1.

    @property
    def mobil(self):
        return (self.rperm)/(self.visc*self.fvf)