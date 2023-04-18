# RESERVOIR SIMULATION MODULES

from ._relperm import RelPerm

from ._cappres import BrooksCorey
from ._cappres import VanGenuchten
from ._cappres import JFunction
from ._cappres import ScanCurves

from ._initialization import ResInit

from ._onephase import OnePhaseImplicit

from ._twophase import TwoPhaseIMPES
from ._twophase import TwoPhaseSS

from ._threephase import ThreePhaseIMPES
from ._threephase import ThreePhaseSS

# ANALYTICAL MODULES

from ._linear import SinglePhaseLinear
from ._linear import MiscibleDisplacement
from ._linear import BuckleyLeverett

from ._radial import Radial
from ._radial import Steady
from ._radial import Transient
from ._radial import PseudoSteady

# from ._green import OnePhaseLineSource
# from ._green import OnePhasePlaneSource
# from ._green import OnePhaseFractureNetwork