from dataclasses import dataclass

import numpy

@dataclass
class Well:
    """
    radius  : wellbore radius, ft
    skin    : skin factor, dimensionless
    time    : time array when to calculate bottom hole pressure, days
    rate    : constant flow rate, STB/day
    press   : bottom hole pressure, psi
    """
    radius  : float = None
    skin    : float = None
    time    : float = None
    rate    : float = None
    press   : float = None

    @property
    def area(self):
        return numpy.pi*self.radius**2