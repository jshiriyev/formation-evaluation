import numpy

class neutron():

    def __init__(self,values,depths=None):
        """Initializes neutron porosity values and depths for porosity calculations.
        If depths values are provided, they must be the same size as values."""
        self.values = values
        self.depths = depths

    def phin(self):
        return self.values

    def phincorr(self,phin,vshale,phinsh=0.35):
        """Calculates shale corrected neutron porosity based on shale volume (vshale) and
        phinsh (neutron porosity at shale).
        """
        phin_corrected = phin-vshale*phinsh

        phin_corrected[phin_corrected>1] = 1
        phin_corrected[phin_corrected<0] = 0

        return phin_corrected

    def _gamma_capture_total(self,phi_clean,phi_shale,ngl_clean=None,ngl_shale=None):
        """The porosity based on gamma detection:
        
        phi_clean    :  porosity in the clean formation
        phi_shale    :  porosity in the adjacent shale

        ngl_clean    :  NGL reading in the clean formation
        ngl_shale    :  NGL reading in the adjacent shale
        
        """

        if ngl_clean is None:
            ngl_clean = self.NGL.min()

        if ngl_shale is None:
            ngl_shale = self.NGL.max()

        normalized = (self.NGL.vals-ngl_clean)/(ngl_shale-ngl_clean)

        normalized[normalized<=0] = 0
        normalized[normalized>=1] = 1

        PHIT = phi_clean+(phi_shale-phi_clean)*normalized

        info = 'Total porosity calculated from neutron-gamma-log.'

        return LasCurve(
            depth = self.NGL.depth,
            vals = PHIT,
            head = 'PHIT',
            unit = '-',
            info = info)

    def _gamma_capture_effective(self,phi_clean,phi_shale,**kwargs):
        """
        shale_volume :  it is required for the calculation of effective porosity,
                        and it can be calculated from etiher GR or SP logs.
        """

        PHIT = self._gamma_capture_total(phi_clean,phi_shale,**kwargs)

        PHIE = PHIT.vals-self.VSH.vals*phi_shale

        info = 'Effective porosity calculated from neutron-gamma-log.'

        return LasCurve(
            depth = self.NGL.depth,
            vals = PHIE,
            head = 'PHIE',
            unit = '-',
            info = info)

    def _neutron_count(self,a,b):
        """The porosity based on the neutron count is given by:
        
        nnl = a-b*log(phi)
        
        curve   :  neutron-neutron-logging curve, the slow neutrons counted

        a       :  empirical constants determined by appropriate calibration
        b       :  empirical constants determined by appropriate calibration

        phi     :  porosity

        """

        porosity = {}

        total = 10**((a-curve.vals)/b)

        return total

class density():

    def __init__(self,values,depths=None):
        """Initializes bulk density values and depths for porosity calculations.
        If depths values are provided, they must be the same size as values."""
        self.values = values
        self.depths = depths

    def phid(self,rhomat=2.65,rhofluid=1.0):
        """Calculates porosity based on bulk density, matrix density (rhomat), and fluid density (rhofluid)."""
        phi_density = (rhomat-self.values)/(rhomat-rhofluid)

        phi_density[phi_density>1] = 1
        phi_density[phi_density<0] = 0

        return phi_density

    def phidcorr(self,phid,vshale,phidsh=0.1):
        """Calculates shale corrected density porosity based on shale volume (vshale) and
        phidsh (density porosity at shale).
        """
        phid_corrected = phid-vshale*phidsh

        phid_corrected[phid_corrected>1] = 1
        phid_corrected[phid_corrected<0] = 0

        return phid_corrected

class sonic():

    def __init__(self,values,depths):
        """Initializes sonic transit times and depths for porosity calculations.
        If depths values are provided, they must be the same size as values."""
        self.values = values
        self.depths = depths

    def phis(self,dtmat,dtfluid,dtshale=100):
        """Calculates porosity based on transit times, matrix transit time (dtmat),
        fluid transit time (dtfluid), and (optional) adjacent shale transit time (dtshale)."""
        phi_sonic = (self.values-dtmat)/(dtfluid-dtmat)*(100/dtshale)

        phi_sonic[phi_sonic>1] = 1
        phi_sonic[phi_sonic<0] = 0

        return phi_sonic