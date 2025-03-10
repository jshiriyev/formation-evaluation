import numpy

class MotifPattern:
    """
    A class representing a repetitive patch pattern with customizable dimensions and spacing.

    Attributes:
    ----------
    element (str): The shape used for the pattern.

    length (float): Length of each pattern figure. Must be positive.
    height (float): Height of each pattern figure. Must be positive.

    length_ratio (float): Spacing multiplier between patterns along the length.
    height_ratio (float): Spacing multiplier between patterns along the height.

    offset_ratio (float): Horizontal shift for every other row (0 = no shift, 0.5 = half length).
    tilted_ratio (float): Tilt applied to the ceiling of the figure (0 = no tilt, 1 = full length).
    """

    def __init__(self,
    	element : str, *,
    	length : float = 0.8,
    	height : float = 0.4,
    	length_ratio : float = 1.0,
    	height_ratio : float = 1.0,
    	length_extern : float = None,
    	height_extern : float = None,
    	offset_ratio : float = 0.5,
    	tilted_ratio : float = 0.,
    	tilted_length : float = None,
    	radius : float = None,
    	params : dict = None):

	    self.element = element

	    self.length = length
	    self.height = height

	    self.length_ratio = length_ratio
	    self.height_ratio = height_ratio

	    self.length_extern = length_extern
	    self.height_extern = height_extern

	    self.offset_ratio = offset_ratio
	    self.tilted_ratio = tilted_ratio

	    self.tilted_length = tilted_length

	    self.radius = radius
	    self.params = params

    @property
    def length_extern(self):
        """Returns the external length that includes spacing between elements."""
        return self._length_extern

    @length_extern.setter
    def length_extern(self,value):
    	"""Setter for the external length that includes spacing between elements."""
    	self._length_extern = self.length*self.length_ratio if value is None else value

    @property
    def height_extern(self):
        """Returns the external height that includes spacing between elements."""
        return self._height_extern

    @height_extern.setter
    def height_extern(self,value):
    	"""Setter for the external height that includes spacing between elements."""
    	self._height_extern = self.height*self.height_ratio if value is None else value

    @property
    def tilted_length(self):
        """Returns the tilted length based on the tilt ratio."""
        return self._tilted_length

    @tilted_length.setter
    def tilted_length(self,value):
    	"""Setter for the tilted length based on the tilt ratio."""
    	if value is None:
    		try:
    			self._tilted_length = self.length*self.tilted_ratio
    		except TypeError:
    			self._tilted_length = None
    	else:
    		self._tilted_ratio = value

    @property
    def radius(self):
        """Returns the effective radius based on length and height."""
        return self._radius

    @radius.setter
    def radius(self,value):
    	"""Setter for the effective radius based on length and height."""
    	if value is None:
    		try:
    			self._radius = numpy.sqrt(self.length*self.height)/2
    		except TypeError:
    			self._radius = None
    	else:
    		self._radius = value

    @property
    def params(self):
    	"""Returns the additional parameters used in the plotting."""
    	return self._params

    @params.setter
    def params(self,value):
        """Setter for the additional parameters used in the plotting."""
        self._params = {} if value is None else value
    
class Motifs:

    irons = MotifPattern(**{
        "element" : "circle",
        "length" : 0.2/1.5,
        "height" : 0.2/1.5,
        "length_ratio" : 6.,
        "height_ratio" : 1.5,
        "offset_ratio" : 0.5,
        "params" : dict(edgecolor='black',facecolor="red"),
        })

    shale = MotifPattern(**{
        "element" : "line",
        "length" : 0.8/2,
        "height" : 0.,
        "length_ratio" : 2.0,
        "length_extern" : 0.8,
        "height_extern" : 0.2,
        "offset_ratio" : 0.5,
        "params" : dict(edgecolor='black',fill=None,),
        })

    chert = MotifPattern(**{
        "element" : "triangle",
        "length" : 0.8/3,
        "height" : 0.2/1.5,
        "length_ratio" : 3.,
        "height_ratio" : 1.5,
        "offset_ratio" : 0.5,
        "tilted_ratio" : 0.,
        "params" : dict(edgecolor='black',facecolor="white",),
        })

    brick = MotifPattern(**{
        "element" : "quadrupe",
        "length" : 0.8,
        "height" : 0.2,
        "length_ratio" : 1.,
        "height_ratio" : 1.,
        "offset_ratio" : 0.5,
        "tilted_ratio" : 0.,
        "params" : dict(edgecolor='black',fill=None,),
        })

    rhomb = MotifPattern(**{
        "element" : "quadrupe",
        "length" : 0.8,
        "height" : 0.2,
        "length_ratio" : 1.,
        "height_ratio" : 1.,
        "offset_ratio" : 0.5,
        "tilted_ratio" : 0.25,
        "params" : dict(edgecolor='black',fill=None,),
        })

if __name__ == "__main__":

	motif = MotifPattern("triangle")

	print(Motifs.shale.height)