from dataclasses import dataclass, field

class PropDict:
    """It is a class representation of petrophysical property dictionary."""
    def __init__(self,**data):
        self.__dict__.update(**data)  # Store dictionary keys as attributes

    def __getitem__(self, key):
        raise TypeError("Use attribute access instead of item access.")

    def __repr__(self):
        return f"{self.__class__.__name__}({self.__dict__})"

@dataclass
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
    element : str = None

    length : float = 0.8
    height : float = 0.4

    length_ratio  : float = 1.
    height_ratio  : float = 1.

    offset_ratio  : float = 0.5
    tilted_ratio  : float = 0.

    params : field(default_factory=dict) = None

    def __post_init__(self):
        """Validates input parameters and stores additional keyword arguments."""
        self.params = {} if self.params is None else self.params

    @property
    def extern_length(self):
        """Returns the effective external length, including spacing."""
        return self.length*self.length_ratio

    @property
    def extern_height(self):
        """Returns the effective external height, including spacing."""
        return self.height*self.height_ratio

    @property
    def tilted_length(self):
        """Returns the effective tilted length based on the tilt ratio."""
        return self.length*self.tilted_ratio

class Motifs:

    shale = MotifPattern(**{
        "element" : "fissure",
        "length" : 0.8/2,
        "height" : 0.2/20.,
        "length_ratio" : 2.,
        "height_ratio" : 20.,
        "offset_ratio" : 0.5,
        "tilted_ratio" : None,
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

class Lithology:

    _dict = dict(
        matrix = PropDict(**{"facecolor":"gray","hatch":"xx","motifs":()}),
        shale = PropDict(**{"facecolor":"gray","hatch":"--","motifs":()}),
        shale_free = PropDict(**{"facecolor":"navajowhite","hatch":"||","motifs":()}),
        shaly_sandstone = PropDict(**{"facecolor":"#F4A460","hatch":"...","motifs":(Motifs.shale,)}),
        calcareous_shale = PropDict(**{"facecolor":"gray","hatch":None,"motifs":()}),
        sandstone = PropDict(**{"facecolor":"#F4A460","hatch":"...","motifs":()}),
        sandy_shale = PropDict(**{"facecolor":"brown","hatch":None,"motifs":()}),
        limestone = PropDict(**{"facecolor":"#2BFFFF","hatch":None,"motifs":(Motifs.brick,)}),
        dolomite = PropDict(**{"facecolor":"#E277E3","hatch":None,"motifs":(Motifs.rhomb,)}),
        chert = PropDict(**{"facecolor":"white","hatch":None,"motifs":(Motifs.chert,)}),
        dolomitic_limestone = PropDict(**{"facecolor":"#2BFFFF","hatch":None,"motifs":(Motifs.brick,)}),
        shaly_limestone = PropDict(**{"facecolor":"#2BFFFF","hatch":None,"motifs":(Motifs.brick,Motifs.shale)}),
        cherty_dolomite = PropDict(**{"facecolor":"#E277E3","hatch":None,"motifs":(Motifs.rhomb,Motifs.chert)}),
        shaly_dolomite = PropDict(**{"facecolor":"#E277E3","hatch":None,"motifs":(Motifs.rhomb,Motifs.shale)}),
        dolomitic_shale = PropDict(**{"facecolor":"gray","hatch":None,"motifs":()}),
        cherty_limestone = PropDict(**{"facecolor":"#2BFFFF","hatch":None,"motifs":(Motifs.brick,Motifs.chert)}),
        cherty_dolomitic_limestone = PropDict(**{"facecolor":"#E277E3","hatch":None,"motifs":(Motifs.brick,Motifs.chert)}),
        anhydrite = PropDict(**{"facecolor":"#DAA520","hatch":"xx","motifs":()}),
        halite = PropDict(**{"facecolor":"#00FF00","hatch": "+","motifs":()}),
        salt = PropDict(**{"facecolor":"#00FF00","hatch": "+","motifs":()}),
        gypsum = PropDict(**{"facecolor":"#9370DB","hatch":"\\\\","motifs":()}),
        ironstone = PropDict(**{"facecolor":"gray","hatch":'O',"motifs":()}),
        coal = PropDict(**{"facecolor":"black","hatch":None,"motifs":()}),
    )

    @classmethod
    def get(cls,key):
        return cls._dict[key]

    @classmethod
    @property
    def len(cls):
        return len(cls._dict)

    @classmethod
    def items(cls):
        for key,value in cls._dict.items():
            yield key,value

class Porespace:

    _dict = dict(
        total = PropDict(**dict(facecolor="white",hatch="OO")),
        liquid = PropDict(**dict(facecolor="blue",hatch="OO")),
        water = PropDict(**dict(facecolor="steelb",hatch="OO")),
        water_clay_bound = PropDict(**dict(facecolor="lightskyblue",hatch="XX")),
        water_capillary_bound = PropDict(**dict(facecolor="lightsteelblue",hatch="XX")),
        water_irreducible = PropDict(**dict(facecolor="lightblue",hatch="XX")),
        water_movable = PropDict(**dict(facecolor="aqua",hatch="..")),
        fluid_movable = PropDict(**dict(facecolor="teal",hatch="..")),
        hydrocarbon = PropDict(**dict(facecolor="green",hatch="OO")),
        gas = PropDict(**dict(facecolor="lightco",hatch="OO")),
        gas_residual = PropDict(**dict(facecolor="indianred",hatch="XX")),
        gas_movable = PropDict(**dict(facecolor="red",hatch="..")),
        gas_condensate = PropDict(**dict(facecolor="firebrick",hatch="OO.")),
        oil = PropDict(**dict(facecolor="seagr",hatch="oo")),
        oil_residual = PropDict(**dict(facecolor="forestgreen",hatch="XX")),
        oil_movable = PropDict(**dict(facecolor="limegreen",hatch="..")),
    )

    @classmethod
    def get(cls,key):
        return cls._dict[key]

    @classmethod
    @property
    def len(cls):
        return len(cls._dict)

    @classmethod
    def items(cls):
        for key,value in cls._dict.items():
            yield key,value

if __name__ == "__main__":

    print(Lithology.get("cherty_dolomitic_limestone").facecolor)
    # print(Motifs.rhomb)
    # print(Porespace.total)

    print(Lithology.len)

    # for key,value in Lithology.items():
    #     print(key)