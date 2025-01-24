from dataclasses import dataclass

import numpy

@dataclass
class RRock:
    """
    perm    : permeability in mD
    poro    : porosity
    height  : formation height, ft
    comp    : rock compressibility, 1/psi
    """
    perm    : float = None
    poro    : float = None
    comp    : float = None
    height  : float = None
    radius  : float = None

    @property
    def area(self):
        return numpy.pi*self.radius**2