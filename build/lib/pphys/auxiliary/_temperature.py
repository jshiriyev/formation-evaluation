import numpy

class Temperature:

    def __init__(self,unit_system="field",surface=None,gradient=None):
        """Initializes temperature parameters for field and international units.

        unit_system : Unit system for temperature parameters, field or international

        surface     : The average temperature of the sea surface is about 20°C (68°F),
            but it ranges from more than 30°C (86°F) in warm tropical regions
            to less than 0°C at high latitudes. Input must be [°C] or [°F],
            depending on the unit system.

        gradient    : Worldwide average geothermal gradients changes from 0.024 to 0.041°C/m
            (0.013-0.022°F/ft), with extremes outside this range. Input must be
            [°C/m] or [°F/ft], depending on the unit system.

        """
        self.unit_system    = unit_system
        self.surface        = surface
        self.gradient       = gradient

    @property
    def unit_system(self):
        return self._unit_system

    @property
    def surface(self):
        return self._surface

    @property
    def gradient(self):
        return self._gradient

    @unit_system.setter
    def unit_system(self,value:str):

        self._unit_system = "field" if value is None else value

    @surface.setter
    def surface(self,value:float):

        if self.unit_system == "international":
            self._surface = 20 if value is None else value       # degC

        elif self.unit_system == "field":
            self._surface = 68 if value is None else value       # degF

    @gradient.setter
    def gradient(self,value:float):

        if self.unit_system == "international":
            self._gradient = 0.024 if value is None else value   # degC/m

        elif self.unit_system == "field":
            self._gradient = 0.013 if value is None else value   # degF/ft

    def __call__(self,depths:numpy.ndarray,depth_unit=None,surface_depth:float=0.):
        """Returns the temperature values (in the unit defined based on instance's unit_system)
        at input depths. The depth unit is meter for the international unit system and feet
        for the field unit system.
        """
        depths = numpy.asarray(depths)

        if depth_unit is None:
            return self.surface+self.gradient*(depths-surface_depth)

        if self.unit_system == "international" and depth_unit == "feet":
            depths,surface_depth = depths*0.3048 ,surface_depth*0.3048 
        elif self.unit_system == "field" and depth_unit == "meter":
            depths,surface_depth = depths*3.28084,surface_depth*3.28084

        return self.surface+self.gradient*(depths-surface_depth)

    @staticmethod
    def get_gradient(depth1,temp1,depth2,temp2):
        """Returns the temperature gradient based on two different points where the values are
        available by assuming linear relationship between depth and temperature.
        """
        return (temp2-temp1)/(depth2-depth1)

    @staticmethod
    def F2C(values:numpy.ndarray):
        """Converts the temperature from Fahrenheit to Celsius."""
        return (numpy.asarray(values)-32)*5/9

    @staticmethod
    def C2F(values:numpy.ndarray):
        """Converts the temperature from Celsius to Fahrenheit."""
        return numpy.asarray(values)*9/5+32

    @staticmethod
    def resistivity(res1,temp1,temp2,temp_unit="F"):
        """Calculates the resistivity values for temp2 values."""

        if temp_unit == "C":
            temp1,temp2 = C2F(temp1),C2F(temp2)

        elif temp_unit == "F":
            temp1,temp2 = numpy.asarray(temp1),numpy.asarray(temp2)

        else:
            raise "The temp_unit can be either C or F."

        return res1*(temp1+6.77)/(temp2+6.77)

    @staticmethod
    def horner(temps:numpy.ndarray,delta_time:numpy.ndarray,cooling_time:float):
        """
        Corrects the logged BHT to real formation temperatures based on Horner approach

        Measurements of temperature made by wireline logs at increasing times after
        fluid circulation has stopped are closer and closer to the real formation temperature.
        
        temps           : the measured temperature (at a given depth) from each of
                          several logging runs

        delta_time      : the time after circulation that the borehole has had to
                          partially reheat

        cooling_time    : the length of time that the borehole was subjected to
                          the cooling effects of the fluid

        Returns the formation temperature.
        """
        temps,delta_time = numpy.asarray(temps),numpy.asarray(delta_time)

        X = numpy.log10((cooling_time+delta_time)/delta_time)

        _,intercept = numpy.polyfit(X,temps,1)
        
        return intercept

if __name__ == "__main__":

    t = Temperature(unit_system="field")

    print(t.unit_system)

    print(t.surface)

    print(t.gradient)

    depths = [100,200,300,400]

    print(t(depths,depth_unit="meter"))

    print(depths)