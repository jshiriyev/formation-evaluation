from dataclasses import dataclass

@dataclass
class Temperature:
    """Returns temperature parameters for field and international units.

    surf    : The average temperature of the sea Tsurf is about 20°C (68°F),
              but it ranges from more than 30°C (86°F) in warm tropical regions
              to less than 0°C at high latitudes. Input must be [°C] or [°F],
              respectively.

    grad    : Worldwide average geothermal Tgrads changes from 0.024 to 0.041°C/m
              (0.013-0.022°F/ft), with extremes outside this range. Input must be
              [°C/m] or [°F/ft], respectively.

    unit    : Unit for temperature parameters, field and international

    """

    surf : float = 68.0
    grad : float = 0.013
    unit : str   = 'field'

    def linear(self,unit="field",Tsurf=None,Tsurfdepth=0,Tgrad=None,Tmax=None,Tmaxdepth=None):
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

    @staticmethod
    def settings(unit="field",Tsurf=None,Tgrad=None):

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

def Horner():

    pass

def Resistivity():

    pass

if __name__ == "__main__":

    pass