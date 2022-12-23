import numpy

class gas():

    """
    All the equations are based on the Tarek Ahmed's reservoir engineering book, Chapter 2.

    - A gas is defined as a homogeneous fluid of low viscosity and density
    that has no definite volume but expands to completely fill the vessel in
    which it is placed.

    - Generally, the natural gas is a mixture of hydrocarbon and
    nonhydrocarbon gases.

    - The hydrocarbon gases that are normally found in a natural gas are
    methanes, ethanes, propanes, butanes, pentanes, and small amounts of
    hexanes and heavier.

    - The nonhydrocarbon gases (i.e., impurities) include carbon dioxide,
    hydrogen sulfide, and nitrogen.

    01. properties of natural gases
    02. behavior of ideal gases
    03. behavior of real gases
    04. effect of non-hydrocarbon components on z-factor
    05. non-hydrocarbon adjustment methods
    06. correction for high-molecular-weight gases
    07. direct calculation of compressibility factors
    08. compressibility of natural gases
    09. gas formation volume factor
    10. gas viscosity
    11. methods of calculating the viscosity of natural gases
    
    """

    p_SC_FU = 14.7  # pressure at standard conditions, psi
    T_SC_FU = 60.0  # temperature at standard conditions, Fahrenheit

    R_SI = 8.31446261815324 # universal gas constant, (Pa*m3)/(mol*Kelvin)
    R_FU = 10.731577089016  # universal gas constant, (psi*ft3)/(lbmol*Rankine)

    M_air = 28.96

	def __init__(self,units='SI'):

		self.units = units

    def get_molecular_weight_apparent(self,mole_fraction,molecular_weight):

        return numpy.sum(mole_fraction*molecular_weight)

    def get_specific_gravity(self,standard_conditions=False):

        if not standard_conditions:
            return (density)/(density_of_air)
        else:        
            # Assuming that the behavior of both the gas mixture and the air is
            # described by the ideal gas equation at the standard conditions:
            return (molecular_weight_apparent)/(molecular_weight_air)

    def get_pseudo_critical_properties(self,
        specific_gravity=None,
        system="Natural Gas",
        mole_fractions=None,
        temperature_pseudo_criticals=None,
        pressure_pseudo_criticals=None,
        H2S_mole_fraction=0.0,
        CO2_mole_fraction=0.0,
        N2_mole_fraction=0.0):

        if specific_gravity is None:
            tpc,ppc = self._pseudo_critical_mole_fraction(mole_fractions,temperature_pseudo_criticals,pressure_pseudo_criticals)
        elif system=="Natural Gas":
            tpc,ppc = self._pseudo_critical_natural_gas(specific_gravity)
        elif system=="Gas Condensate":
            tpc,ppc = self._pseudo_critical_gas_condensate(specific_gravity)

        nonHC_mole_fraction = H2S_mole_fraction+CO2_mole_fraction+N2_mole_fraction

        if nonHC_mole_fraction>0:

            if correction_method == "WA": # Wichert-Aziz Correction Method
                tpc,ppc = self._pseudo_critical_correction_wichert_aziz(
                    tpc,ppc,H2S_mole_fraction,CO2_mole_fraction)
            elif correction_method == "CKB": # Carr-Kobayashi-Burrows Correction Method
                tpc,ppc = self._pseudo_critical_correction_carr_kobayashi_burrows(
                    tpc,ppc,H2S_mole_fraction,CO2_mole_fraction,N2_mole_fraction)

        return tpc,ppc

    def _pseudo_critical_natural_gas(self,specific_gravity):
        """It calculates pseudo-critical temperature and pressure for natural gas systems based on specific gravity."""

        tpc = 168+325*specific_gravity-12.5*specific_gravity**2
        ppc = 677+15*specific_gravity-37.5*specific_gravity**2

        return tpc,ppc

    def _pseudo_critical_gas_condensate(self,specific_gravity):
        """It calculates pseudo-critical temperature and pressure for gas condensate systems based on specific gravity."""

        tpc = 1887+33*specific_gravity-71.5*specific_gravity**2
        ppc = 706-51.7*specific_gravity-11.1*specific_gravity**2

        return tpc,ppc

    def _pseudo_critical_mole_fraction(self,mole_fractions,temperature_pseudo_criticals,pressure_pseudo_criticals):
        """It calculates pseudo-critical temperature and pressure based on mole fraction and pseudo properties of each component."""

        tpc = numpy.sum(mole_fractions*temperature_pseudo_criticals)
        ppc = numpy.sum(mole_fractions*pressure_pseudo_criticals)

        return tpc,ppc

    def _pseudo_critical_correction_wichert_aziz(self,tpc,ppc,H2S=0.0,CO2=0.0):
        """It corrects pseudo-critical temperature and pressure based on the non-hydrocarbon mole fraction."""

        A,B = H2S+CO2,H2S
        
        epsilon = 120*(A**0.9-A**1.6)+15*(B**0.5-B**4.0)

        tpc_dash = tpc-epsilon
        ppc_dash = ppc*tpc_dash/(tpc+B*(1-B)*epsilon)

        tpc,ppc = tpc_dash,ppc_dash

        return tpc,ppc

    def _pseudo_critical_correction_carr_kobayashi_burrows(self,tpc,ppc,H2S=0.0,CO2=0.0,N2=0.0):
        """It corrects pseudo-critical temperature and pressure based on the non-hydrocarbon mole fraction."""

        tpc = tpc-80*CO2+130*H2S-250*N2
        ppc = ppc+440*CO2+600*H2S-170*N2

        return tpc,ppc

    def _pseudo_critical_correction_high_molecular_weight(self):

        pass

    def get_zfactor(self,temperature,pressure,method="Hall-Yarborough",**kwargs):

        tpc,ppc = self.get_pseudo_critical_properties(**kwargs)

        tpr,ppr = temperature/tpc,pressure/ppc

        if method=="Hall-Yarborough":
            zfactor = self._zfactor_hall_yarborough(tpr,ppr,**kwargs)
        elif method=="Dranchuk-Abu-Kassem":
            zfactor = self._zfactor_dranchuk_abu_kassem(tpr,ppr,**kwargs)
        elif method=="Dranchuk-Purvis-Robinson":
            zfactor = self._zfactor_dranchuk_purvis_robinson(tpr,ppr,**kwargs)

        return zfactor

    def _zfactor_hall_yarborough(self,tpr,ppr,tol=1e-12,nitermax=100):
        """It calculates the z-factor based on the reduced temperature and pressure."""

        if tpr<1:
            raise Warning("Hall Yarborough method is not recommended for \
                application if pseudo-reduced temperature is less than one.")

        X1 = -0.06125*ppr/tpr*numpy.exp(-1.2*(1-1/tpr)**2)
        X2 = 14.76/tpr-9.76/tpr**2+4.58/tpr**3
        X3 = 90.7/tpr-242.2/tpr**2+42.4/tpr**3
        X4 = 2.18+2.82/tpr

        FYF = lambda Y: X1+(Y+Y**2+Y**3+Y**4)/(1-Y)**3-X2*Y**2+X3*Y**X4
        FYP = lambda Y: (1+4*Y+4*Y**2-4*Y**3+Y**4)/(1-Y)**4-2*X2*Y+X3*X4*Y**(X4-1)

        Yo = 0.0125*ppr/tpr*numpy.exp(-1.2*(1-1/tpr)**2) # initial guess for Y

        for n in range(nitermax):

            Yn = Yo-FYF(Yo)/FYP(Yo)

            if numpy.abs(Yo-Yn)<tol:
                break
            else:
                Yo = Yn

        else:

            raise Warning("Could not converge to the correct value of Y for the \
                given nitermax and tolerance!")

        zfactor = (0.06125*ppr/tpr/Yn)*numpy.exp(-1.2*(1-1/tpr)**2)

        return zfactor

    def _zfactor_dranchuk_abu_kassem(self,tpr,ppr):
        """It calculates the z-factor based on the reduced temperature and pressure."""

        if tpr<1.00 or tpr>3.0:
            raise Warning(f"The recommended range of {tpr=} for Dranchuk-Abu-Kassem method is 1.0<Tpr<3.0.")

        if ppr<0.20 or ppr>30.0:
            raise Warning(f"The recommended range of {ppr=} for Dranchuk-Abu-Kassem method is 0.2<Ppr<30.0.")

        A01 = +0.3265
        A02 = -1.0700
        A03 = -0.5339
        A04 = +0.01569
        A05 = -0.05165
        A06 = +0.5475
        A07 = -0.7361
        A08 = +0.1844
        A09 = +0.1056
        A10 = +0.6134
        A11 = +0.7210

    def _zfactor_dranchuk_purvis_robinson(self,tpr,ppr):
        """It calculates the z-factor based on the reduced temperature and pressure."""

        if tpr<1.05 or tpr>3.0:
            raise Warning(f"The recommended range of {tpr=} for Dranchuk-Purvis-Robinson method is 1.05<Tpr<3.0.")

        if ppr<0.20 or ppr>3.0:
            raise Warning(f"The recommended range of {ppr=} for Dranchuk Purvis Robinson method is 0.2<Ppr<3.0.")

        A01 = +0.31506237
        A02 = -1.0467099
        A03 = -0.57832720
        A04 = +0.53530771
        A05 = -0.61232032
        A06 = -0.10488813
        A07 = +0.68157001
        A08 = +0.68446549

    def get_density(self):

        return (pressure*molecular_weight)/(zfactor*self.R_FU*temperature)

    def get_specific_volume(self,**kwargs):

        return 1/self.get_density(**kwargs)

    def get_compressibility_isothermal(self):

        pass

    def get_fvf(self):

        pass

    def get_expansion_factor(self):

        pass

    def get_viscosity(self,method="Carr-Kobayashi-Burrows"):

        if method=="Carr-Kobayashi-Burrows":
            viscosity = self._viscosity_carr_kobayashi_burrows()
        elif method=="Lee-Gonzalez-Eakin":
            viscosity = self._viscosity_lee_gonzalez_eakin()

        return viscosity

    def _viscosity_carr_kobayashi_burrows(self):

        return viscosity

    def _viscosity_lee_gonzalez_eakin(self):

        return viscosity

class oil():

    """
    12. properties of crude oil systems
    13. crude oil gravity
    14. specific gravity of the solution gas
    15. gas solubility
    16. bubble-point pressure
    17. oil formation volume factor
    18. isothermal compressibility coefficient of crude oil
    19. oil formation volume factor for undersaturated oils
    20. crude oil density
    21. crude oil viscosity
    22. methods of calculating viscosity of the dead oil
    23. methods of calculating the saturated oil viscosity
    24. methods of calculating the viscosity of the undersaturated oil
    25. surface/interfacial tension
    """

    def __init__(self):

        pass

    def get_gravity(self):
        
        pass

    def get_solution_gas_gravity(self):
        
        pass

    def get_gas_solubility(self):
        
        pass

    def get_bpp(self):
        
        pass

    def get_fvf(self):
        
        pass

    def get_isothermal_compressibility(self):
        
        pass

    def get_density(self):
        
        pass

    def get_viscosity(self):
        
        pass

class water():

    """
    26. properties of reservoir water
    27. water formation volume factor
    28. water viscosity
    29. gas solubility in water
    30. water isothermal compressibility
    """

    def __init__(self):

        pass

    def get_fvf(self):

        pass

    def get_viscosity(self):

        pass

    def get_gas_solubility(self):

        pass

    def get_isothermal_compressibility(self):

        pass

class component():

	def __init__(self):

		pass

class mixture():

    def __init__(self,number):

        self.number = number

        self.itemnames = []
        self.molarweight = []
        self.density = []
        self.compressibility = []
        self.viscosity = []
        self.fvf = []

    def set_names(self,*args):

        for arg in args:
            self.itemnames.append(arg)

    def set_molarweight(self,*args):

        for arg in args:
            self.molarweight.append(arg)

    def set_density(self,density1,*args):

        self.density = [density1,]

        for arg in args:
            self.density.append(arg)

    def set_compressibility(self,*args):

        for arg in args:
            self.compressibility.append(arg)

    def set_viscosity(self,*args):

        for arg in args:
            self.viscosity.append(arg)

    def set_fvf(self,*args):

        for arg in args:
            self.fvf.append(arg)