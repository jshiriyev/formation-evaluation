if __name__ == '__main__':
	import _setup

from flow._main import RelPerm
from flow._main import CapPres

from flow._linear import OnePhaseLinear
from flow._linear import OnePhaseLinearMultiComponent
from flow._linear import TwoPhaseLinear

from flow._radial import OnePhaseRadial
from flow._radial import OnePhaseRadialSteady
from flow._radial import OnePhaseRadialTransient
from flow._radial import OnePhaseRadialPseudoSteady

from flow._green import OnePhaseLineSource
from flow._green import OnePhasePlaneSource
from flow._green import OnePhaseFractureNetwork

from flow._simulation import OnePhase
from flow._simulation import TwoPhaseIMPES
from flow._simulation import TwoPhaseSS
from flow._simulation import ThreePhaseIMPES
from flow._simulation import ThreePhaseSS