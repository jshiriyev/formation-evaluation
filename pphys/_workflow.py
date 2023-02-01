from . import cores
from . import wlogs

class WorkFlow():

    def __init__(self,lasfile=None,**kwargs):

        if lasfile is None:
            self.lasfile = LasFile(**kwargs)
        elif isinstance(lasfile,str):
            self.lasfile = loadlas(lasfile,**kwargs)
        elif isinstance(lasfile,LasFile):
            self.lasfile = lasfile

    def set_temps(self,unit="field",Tsurf=None,Tsurfdepth=0,Tgrad=None,Tmax=None,Tmaxdepth=None):
        """
        It will calculate the temperature based on the linear equation
        if it is not measured for every depth.
        
        unit         : unit system to be used for the calculation, field or international
        Tsurf        : temperature at the surface, °F or °C
        Tsurfdepth   : Tsurface depth where we know the temperature, ft or meters
        Tmax         : temperature at maximum depth, °F or °C
        Tmaxdepth    : maximum depth where we know the temperature, ft or meters
        Tgrad        : temperature gradient, °F/ft or °C/m

        """

        if Tmax is not None: #it should mean that Tmaxdepth is not None too

            if Tsurf is None: #it should mean that Tgrad is not None
                Tsurf = Tmax-Tgrad*(Tmaxdepth-Tsurfdepth)
            if Tgrad is None: #it should mean that Tsurf is not None
                Tgrad = (Tmax-Tsurf)/(Tmaxdepth-Tsurfdepth)

        temp = self.temperature(unit=unit,Tsurf=Tsurf,Tgrad=Tgrad)

        Tsurf = temp['Tsurf']
        Tgrad = temp['Tgrad']

        depth = self.lasfile.depth

        if unit == "field":
            cdepth = depth.convert('ft')
        elif unit == "international":
            cdepth = depth.convert('m')

        Temp = Tsurf+Tgrad*(cdepth.vals-Tsurfdepth)

        if unit == "field":
            Tunit = "degF"
        elif unit == "international":
            Tunit = "degC"

        info = f"Linear temperature with {unit} units, {Tsurf=}, {Tsurfdepth=}, {Tgrad=}."

        self.add_curve(vals=Temp,head='TEMP',unit=Tunit,info=info,depth=depth)

        temp['Tsurfdepth'] = Tsurfdepth
        
        self.temp = temp

    def set_perm(self,PHI,method=None):

        PHIE = self[PHI].vals

        PERM = 50*((1-0.13)**2)/(0.13**3)*(PHIE**3)/((1-PHIE)**2)

        depth = self.lasfile.depth

        info = 'Permeability calculated from effective porosity.'

        self.add_curve(vals=PERM,depth=depth,head='PERM',unit='mD',info=info)

    def set_bwv(self,PHI,SW):

        porosity = self[PHI].vals

        saturation = self[SW].vals

        BWV = porosity*saturation

        depth = self.lasfile.depth

        info = 'Bulk water volume.'

        self.add_curve(vals=BWV,depth=depth,head='BWV',unit='-',info=info)

    def __getattr__(self,key):

        return getattr(self.lasfile,key)

    def __setitem__(self,head,curve):

        self.lasfile[head] = curve

    def __getitem__(self,head):

        return self.lasfile[head]

    def __call__(self,**kwargs):
        """It is calling the interpretation method for the specified curve(s)."""

        if len(kwargs) != 1:
            raise "Number of optional arguments must be one specifying method and head dictionary."

        method,heads = kwargs.popitem()

        if not isinstance(heads,dict):
            raise "Heads must be dictionary!"

        curves = {}

        for head,curve in heads.items():
            curves[head] = self[curve]

        if method is None:
            return
        elif method.lower() == "sonic":
            return sonic(**curves)
        elif method.lower() == "spotential":
            return spotential(**curves)
        elif method.lower() == "laterolog":
            return laterolog(**curves)
        elif method.lower() == "induction":
            return induction(**curves)
        elif method.lower() == "gammaray":
            return gammaray(**curves)
        elif method.lower() == "density":
            return density(**curves)
        elif method.lower() == "neutron":
            return neutron(**curves)
        elif method.lower() == "nmr":
            return nmr(**curves)
        elif method.lower() == "density-neutron":
            return denneu(**curves)
        elif method.lower() == "sonic-density":
            return sonden(**curves)
        elif method.lower() == "sonic-neutron":
            return sonneu(**curves)
        elif method.lower() == "mn-plot":
            return mnplot(**curves)
        elif method.lower() == "mid-plot":
            return midplot(**curves)
        elif method.lower() == "rhomaa-umaa":
            return rhoumaa(**curves)
        elif method.lower() == "pickett":
            return pickett(**curves)
        elif method.lower() == "hingle":
            return hingle(**curves)

    @staticmethod
    def temperature(unit="field",Tsurf=None,Tgrad=None):
        """Returns temperature parameters for field and international units.
        
        unit    : Unit unit for temperature parameters, field and international

        Tsurf   : The average temperature of the sea Tsurf is about 20°C (68°F),
                  but it ranges from more than 30°C (86°F) in warm tropical regions
                  to less than 0°C at high latitudes. Input must be [°C] or [°F],
                  respectively.

        Tgrad   : Worldwide average geothermal Tgrads changes from 0.024 to 0.041°C/m
                  (0.013-0.022°F/ft), with extremes outside this range. Input must be
                  [°C/m] or [°F/ft], respectively.

        """

        temp = {}

        temp['unit'] = unit

        if unit == "international":
            Tgrad = 0.024 if Tgrad is None else Tgrad   # degC/m
            Tsurf = 20 if Tsurf is None else Tsurf      # degC
        elif unit == "field":
            Tgrad = 0.013 if Tgrad is None else Tgrad   # degF/ft
            Tsurf = 68 if Tsurf is None else Tsurf      # degF

        temp['Tsurf'] = Tsurf
        temp['Tgrad'] = Tgrad

        return temp

    @staticmethod
    def archie(m=2,a=1,Rw=0.01,n=2):

        archie = {}

        archie["m"] = m
        archie["a"] = a
        archie["Rw"] = Rw
        archie["n"] = n

        return archie
