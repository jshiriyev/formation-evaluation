from ._motifs import Motifs

class PropDict:
    """It is a class representation of petrophysical property dictionary."""
    def __init__(self,**data):
        self.__dict__.update(**data)  # Store dictionary keys as attributes

    def __getitem__(self, key):
        raise TypeError("Use attribute access instead of item access.")

    def __repr__(self):
        return f"{self.__class__.__name__}({self.__dict__})"

class Lithology:

    _dict = dict(
        matrix = PropDict(**{"facecolor":"gray","hatch":"xx","motifs":()}),
        shale = PropDict(**{"facecolor":"gray","hatch":"--","motifs":()}),
        shale_free = PropDict(**{"facecolor":"navajowhite","hatch":"||","motifs":()}),
        shaly_sandstone = PropDict(**{"facecolor":"#F4A460","hatch":"...","motifs":(Motifs.shale,)}),
        calcareous_shale = PropDict(**{"facecolor":"gray","hatch":None,"motifs":()}),
        sandstone = PropDict(**{"facecolor":"#F4A460","hatch":"...","motifs":()}),
        sandy_shale = PropDict(**{"facecolor":"#CD9967","hatch":None,"motifs":()}),
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
        ironstone = PropDict(**{"facecolor":"gray","hatch":None,"motifs":(Motifs.irons,)}),
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