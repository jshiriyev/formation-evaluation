import json

if __name__ == "__main__":
    import dirsetup

from textio import header

class gas():
    """
    The hydrocarbon gases that are normally found in a natural gas are
    methanes, ethanes, propanes, butanes, pentanes, and small amounts of
    hexanes and heavier. The nonhydrocarbon gases include carbon dioxide,
    hydrogen sulfide, and nitrogen.
    """

    def __init__(self,name=None,spgr=None,units='SI',**kwargs):
        """
        Gas can be defined based on specific gravity or molecular composition.
        
        First option, specific gravity (spgr) must be defined at standard conditions:
        
        name            : 'natural-gas', 'gas-condensate' or 'custom'.
        spgr            : specific gravity of the gas at standard conditions.
        
        Second option, molecular composition can be defined in dictionary (**kwargs) and it may contain:

        component       : abbreviation of component ('CH4','C2H6','H2S',etc.)
        molefraction    : mole fraction of each component
        moleweight      : molecular weight of each component
        Tcritical       : critical temperature for each component
        Pcritical       : critical pressure for each component
        .               :
        .               :
        .               :

        units           : unit system, options are international system (SI) and field units (FU)

        """

        self.set_library()

        self.units = units

        if spgr is not None and len(kwargs)==0:
            self.composition = header(
                component=name,
                molefraction=1.0,
                moleweight=spgr*self.library["air"]["moleweight"])
        elif spgr is None and len(kwargs)>0:
            self.composition = header(**kwargs)
            self.set_compositional_properties()
        
        if not hasattr(self,"composition"):
            return

        self.methods = {
            "non-hydrocarbon-correction": "",
            "high-molecular-weight-correction": "",
            "viscosity-calculation": "",
            }

        self.set_mole_fraction_sum_to_one()
        # self.set_molecular_weight_apparent()
        # self.set_specific_gravity()
        # self.set_pseudo_critical_properties()

    def set_library(self):

        with open("fluids.json","r") as jsonfile:

            library = json.load(jsonfile)

            self.standard = library['standard-condition']
            self.gasconst = library['gas-constant']
            self.library = library['substances']

    def set_mole_fraction_sum_to_one(self):

        fraction_temp = self.composition.molefraction

        factor = 1/sum(fraction_temp)

        fraction = [frac*factor for frac in fraction_temp]

        self.composition.molefraction = fraction

    def set_compositional_properties(self):

        pass

    def set_molecular_weight_apparent(self):

        molefractions = self.composition.molefraction
        moleweights = self.composition.moleweight

        table = zip(molefractions,moleweights)

        weights = [fraction*weight for fraction,weight in table]

        self.mwapp = sum(weights)

    def set_pseudo_critical_properties(self,nhc_corr="",hmw_corr=""):

        if len(self.composition)==1:
            if self.composition.component=="natural-gas":
                tpc,ppc = self._pseudo_critical_for_natural_gas()
            elif self.composition.component=="gas-condensate":
                tpc,ppc = self._pseudo_critical_for_gas_condensate()
            else:
                raise Warning("Pseudo-critical-properties have not been calculated.")
        elif len(self.composition)>1:
            tpc,ppc = self._pseudo_critical_for_composition()

        try:
            H2S = self.composition['H2S']
        except KeyError:
            H2S_mf = 0
        else:
            H2S_mf = H2S.molefraction

        try:
            CO2 = self.composition['CO2']
        except KeyError:
            CO2_mf = 0
        else:
            CO2_mf = CO2.molefraction

        try:
            N2 = self.composition['N2']
        except KeyError:
            N2_mf = 0
        else:
            N2_mf = N2.molefraction

        if H2S_mf+CO2_mf+N2_mf>0:

            if correction_method == "WA": # Wichert-Aziz Correction Method
                tpc,ppc = self._pseudo_critical_correction_wichert_aziz(
                    tpc,ppc,H2S_mf,CO2_mf)
            elif correction_method == "CKB": # Carr-Kobayashi-Burrows Correction Method
                tpc,ppc = self._pseudo_critical_correction_carr_kobayashi_burrows(
                    tpc,ppc,H2S_mf,CO2_mf,N2_mf)

        self.tpc,self.ppc = tpc,ppc

    def _pseudo_critical_for_natural_gas(self):
        """It calculates pseudo-critical temperature and pressure for
        natural-gas systems based on specific gravity."""

        tpc = 168+325*self.spgr-12.5*self.spgr**2
        ppc = 677+15*self.spgr-37.5*self.spgr**2

        return tpc,ppc

    def _pseudo_critical_for_gas_condensate(self):
        """It calculates pseudo-critical temperature and pressure for
        gas-condensate systems based on specific gravity."""

        tpc = 1887+33*self.spgr-71.5*self.spgr**2
        ppc = 706-51.7*self.spgr-11.1*self.spgr**2

        return tpc,ppc

    def _pseudo_critical_for_composition(self):
        """It calculates pseudo-critical temperature and pressure based on
        mole fraction and pseudo properties of each component."""

        MF = self.composition.molefraction
        TC = self.composition.Tcritical
        PC = self.composition.Pcritical

        tpcs = [frac*T for frac,T in zip(MF,TC)]
        ppcs = [frac*P for frac,P in zip(MF,PC)]

        return sum(tpcs),sum(ppcs)

    def _pseudo_critical_correction_wichert_aziz(self,tpc,ppc,H2S=0.0,CO2=0.0):
        """It corrects pseudo-critical temperature and pressure based on
        the non-hydrocarbon mole fraction."""

        A,B = H2S+CO2,H2S
        
        epsilon = 120*(A**0.9-A**1.6)+15*(B**0.5-B**4.0)

        tpc_dash = tpc-epsilon
        ppc_dash = ppc*tpc_dash/(tpc+B*(1-B)*epsilon)

        tpc,ppc = tpc_dash,ppc_dash

        return tpc,ppc

    def _pseudo_critical_correction_carr_kobayashi_burrows(self,tpc,ppc,H2S=0.0,CO2=0.0,N2=0.0):
        """It corrects pseudo-critical temperature and pressure based on
        the non-hydrocarbon mole fraction."""

        tpc = tpc-80*CO2+130*H2S-250*N2
        ppc = ppc+440*CO2+600*H2S-170*N2

        return tpc,ppc

    def _pseudo_critical_correction_high_molecular_weight(self):

        pass

    def get_molecular_weight_apparent(self):

        pass

    def get_specific_gravity(self):

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

    @property
    def density(self):

        return (pressure*molecular_weight)/(zfactor*self.R_FU*temperature)

    @property
    def spgr(self):
        """The calculation assumes that the behavior of both the gas mixture and
        air is described by the ideal gas equation at standard conditions."""

        self.spgr = self.mwapp/self.library["air"]["moleweight"]

    @property
    def sp_volume(self,**kwargs):

        return 1/self.get_density(**kwargs)
    
    @property
    def cg_isothermal(self):

        pass

    @property
    def fvf(self):

        pass

    @property
    def expansion_factor(self):

        pass

    @property
    def viscosity(self,method="Carr-Kobayashi-Burrows"):

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

class singlephase():

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

class multiphase():

    def __init__(self):

        pass

if __name__ == "__main__":

    fluids = gas(component=['CH4','C2H6'],molefraction=[0.2,0.4])

    print(fluids.composition.molefraction)

    print(fluids.composition['CH4'].molefraction)
    print(len(fluids.composition))

    print(fluids.library['CH4']['moleweight'])