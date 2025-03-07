from dataclasses import dataclass, field

class AttrDict:
    def __init__(self,**data):
        self.__dict__.update(**data)  # Store dictionary keys as attributes

    def __getitem__(self, key):
        raise TypeError("Use attribute access instead of item access.")

    def __repr__(self):
        return f"{self.__class__.__name__}({self.__dict__})"

@dataclass
class PatchPattern:
    """
    A class representing a repetitive patch pattern with customizable dimensions and spacing.

    Attributes:
    ----------
    motive (str): The shape used for the pattern.

    length (float): Length of each pattern figure. Must be positive.
    height (float): Height of each pattern figure. Must be positive.

    length_ratio (float): Spacing multiplier between patterns along the length.
    height_ratio (float): Spacing multiplier between patterns along the height.

    offset_ratio (float): Horizontal shift for every other row (0 = no shift, 0.5 = half length).
    tilted_ratio (float): Tilt applied to the ceiling of the figure (0 = no tilt, 1 = full length).
    """
    motive : str = None

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

class Motives:

    brick = PatchPattern(**{
        "motive" : "brick",
        "length" : 0.8,
        "height" : 0.2,
        "length_ratio" : 1.,
        "height_ratio" : 1.,
        "offset_ratio" : 0.5,
        "tilted_ratio" : 0.,
        "params" : dict(edgecolor='black',facecolor=None,),
        })

    rhomb = PatchPattern(**{
        "motive" : "brick",
        "length" : 0.8,
        "height" : 0.2,
        "length_ratio" : 1.,
        "height_ratio" : 1.,
        "offset_ratio" : 0.5,
        "tilted_ratio" : 0.25,
        "params" : dict(edgecolor='black',facecolor=None,),
        })

    chert = PatchPattern(**{
        "motive" : "triangle",
        "length" : 0.8/3,
        "height" : 0.2/1.5,
        "length_ratio" : 3.,
        "height_ratio" : 1.5,
        "offset_ratio" : 0.5,
        "tilted_ratio" : 0.,
        "params" : dict(edgecolor='black',facecolor="white",),
        })

class Lithology:

    matrix = AttrDict(**{"facecolor":"gray","hatch":"xx","motives":()})
    shale = AttrDict(**{"facecolor":"gray","hatch":"--","motives":()})
    shale_free = AttrDict(**{"facecolor":"navajowhite","hatch":"||","motives":()})
    shaly_sandstone = AttrDict(**{"facecolor":"#F4A460","hatch":"...","motives":()})
    calcareous_shale = AttrDict(**{"facecolor":"gray","hatch":None,"motives":()})
    sandstone = AttrDict(**{"facecolor":"#F4A460","hatch":"...","motives":()})
    sandy_shale = AttrDict(**{"facecolor":"brown","hatch":None,"motives":()})
    limestone = AttrDict(**{"facecolor":"#2BFFFF","hatch":None,"motives":(Motives.brick,)})
    dolomite = AttrDict(**{"facecolor":"#E277E3","hatch":None,"motives":(Motives.rhomb,)})
    chert = AttrDict(**{"facecolor":"white","hatch":None,"motives":(Motives.chert,)})
    dolomitic_limestone = AttrDict(**{"facecolor":"#2BFFFF","hatch":None,"motives":(Motives.brick,)})
    shaly_limestone = AttrDict(**{"facecolor":"#2BFFFF","hatch":None,"motives":(Motives.brick,)})
    cherty_dolomite = AttrDict(**{"facecolor":"#E277E3","hatch":None,"motives":(Motives.rhomb,Motives.chert)})
    shaly_dolomite = AttrDict(**{"facecolor":"#E277E3","hatch":None,"motives":(Motives.rhomb,)})
    dolomitic_shale = AttrDict(**{"facecolor":"gray","hatch":None,"motives":()})
    cherty_limestone = AttrDict(**{"facecolor":"#2BFFFF","hatch":None,"motives":(Motives.brick,Motives.chert)})
    cherty_dolomitic_limestone = AttrDict(**{"facecolor":"#E277E3","hatch":None,"motives":(Motives.brick,Motives.chert)})
    anhydrite = AttrDict(**{"facecolor":"#DAA520","hatch":"xx","motives":(),})
    halite = AttrDict(**{"facecolor":"#00FF00","hatch": "+","motives":(),})
    salt = halite
    gypsum = AttrDict(**{"facecolor":"#9370DB","hatch":"\\\\","motives":(),})
    ironstone = AttrDict(**{"facecolor":"gray","hatch":'O',"motives":(),})
    coal = AttrDict(**{"facecolor":"black","hatch":None,"motives":(),})

class Porespace:

    total = AttrDict(**dict(facecolor="white",hatch="OO"))
    liquid = AttrDict(**dict(facecolor="blue",hatch="OO"))
    water = AttrDict(**dict(facecolor="steelb",hatch="OO"))
    water_clay_bound = AttrDict(**dict(facecolor="lightskyblue",hatch="XX"))
    water_capillary_bound = AttrDict(**dict(facecolor="lightsteelblue",hatch="XX"))
    water_irreducible = AttrDict(**dict(facecolor="lightblue",hatch="XX"))
    water_movable = AttrDict(**dict(facecolor="aqua",hatch=".."))
    fluid_movable = AttrDict(**dict(facecolor="teal",hatch=".."))
    hydrocarbon = AttrDict(**dict(facecolor="green",hatch="OO"))
    gas = AttrDict(**dict(facecolor="lightco",hatch="OO"))
    gas_residual = AttrDict(**dict(facecolor="indianred",hatch="XX"))
    gas_movable = AttrDict(**dict(facecolor="red",hatch=".."))
    gas_condensate = AttrDict(**dict(facecolor="firebrick",hatch="OO."))
    oil = AttrDict(**dict(facecolor="seagr",hatch="oo"))
    oil_residual = AttrDict(**dict(facecolor="forestgreen",hatch="XX"))
    oil_movable = AttrDict(**dict(facecolor="limegreen",hatch=".."))

if __name__ == "__main__":

    print(Lithology.cherty_dolomitic_limestone.motives)
    # print(Motives.rhomb)
    # print(Porespace.total)