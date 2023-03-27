class neutron():

    def __init__(self,NGL=None,VSH=None):
        """Initialization of output signals."""

        self.NGL = NGL
        self.VSH = VSH

    def config(self,observer):
        """Setting tool configuration."""

        self.observer = observer  # gamma capture rate or neutron count

    def phit(self,*args,**kwargs):

        if self.observer.lower() == "gamma":
            func = getattr(self,"_gamma_capture_total")
        elif self.observer.lower() == "neutron":
            func = getattr(self,"_neutron_count_total")

        return func(*args,**kwargs)

    def phie(self,*args,**kwargs):

        if self.observer.lower() == "gamma":
            func = getattr(self,"_gamma_capture_effective")
        elif self.observer.lower() == "neutron":
            func = getattr(self,"_neutron_count_effective")

        return func(*args,**kwargs)

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