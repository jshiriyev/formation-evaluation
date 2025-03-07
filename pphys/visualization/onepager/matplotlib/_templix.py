matrix = dict(
	color = "gray",
	hatch = "xx",
	)

shale = dict(
    facecolor="gray",
    hatch='--',
    motives=(),
    )

shale_free = dict(
	color = "navajowhite",
	hatch = "||",
	)

shaly_sandstone = dict(
    facecolor="#F4A460",
    hatch="...",
    motives=(),
    )

calcareous_shale = dict(
    facecolor="gray",
    hatch=None,
    motives=(),
    )

sandstone = dict(
    facecolor="#F4A460",
    hatch="...",
    motives=(),
    )

sandy_shale = dict(
    facecolor="brown",
    hatch=None,
    motives=(),
    )

limestone = dict(
    facecolor="#2BFFFF",
    hatch=None,
    motives=("brick",),
    )

dolomite = dict(
    facecolor="#E277E3",
    hatch=None,
    motives=("rhomb",),
    )

chert = dict(
    facecolor="white",
    hatch=None,
    motives=("chert",),
    )

dolomitic_limestone = dict(
    facecolor="#2BFFFF",
    hatch=None,
    motives=("brick"),
    )

shaly_limestone = dict(
    facecolor="#2BFFFF",
    hatch=None, # it is not None
    motives=("brick",),
    )

cherty_dolomite = dict(
    facecolor="#E277E3",
    hatch=None,
    motives=("rhomb","chert"),
    )

shaly_dolomite = dict(
    facecolor="#E277E3",
    hatch=None,
    motives=("rhomb",),
    )

dolomitic_shale = dict(
    facecolor="gray",
    hatch=None,
    motives=(),
    )

cherty_limestone = dict(
    facecolor="#2BFFFF",
    hatch=None,
    motives=("brick","chert"),
    )

cherty_dolomitic_limestone = dict(
    facecolor="#E277E3",
    hatch=None,
    motives=(brick,chert),
    )

anhydrite = dict(
    facecolor="#DAA520",
    hatch="xx",
    motives=(),
    )

halite = dict(
    facecolor="#00FF00",
    hatch= "+",
    motives=(),
    )

salt = halite

gypsum = dict(
    facecolor="#9370DB",
    hatch="\\\\",
    motives=(),
    )

ironstone = dict(
    facecolor="gray",
    hatch='O',
    motives=(),
    )

coal = dict(
    facecolor="black",
    hatch=None,
    motives=(),
    )

## PORE SPACE

pore_volume = dict(
	color = "white",
	hatch = "OO",
	)

liquid = dict(
	color = "blue",
	hatch = "OO",
	)

water = dict(
	color = "steelb",
	hatch = "OO",
	)

water_clay_bound = dict(
	color = "lightskyblue",
	hatch = "XX",
	)

water_capillary_bound = dict(
	color = "lightsteelblue",
	hatch = "XX",
	)

water_irreducible = dict(
	color = "lightblue",
	hatch = "XX",
	)

water_movable = dict(
	color = "aqua",
	hatch = "..",
	)

fluid_movable = dict(
	color = "teal",
	hatch = ".."
	)

hydrocarbon = dict(
	color = "green",
	hatch = "OO",
	)

gas = dict(
	color = "lightco",
	hatch = "OO",
	)

gas_residual = dict(
	color = "indianred",
	hatch = "XX",
	)

gas_movable = dict(
	color = "red",
	hatch = "..",
	)

gas_condensate = dict(
	color = "firebrick",
	hatch = "OO."
	)

oil = dict(
	color = "seagr",
	hatch = "oo",
	)

oil_residual = dict(
	color = "forestgreen",
	hatch = "XX",
	)

oil_movable = dict(
	color = "limegreen",
	hatch = "..",
	)

## PATTERNS

brick = dict(
    motive="brick",
    length=0.8,
    height=0.2,
    length_ratio=1.,
    height_ratio=1.,
    offset_ratio=0.5,
    tilted_ratio=0.,
    params = dict(edgecolor='black',facecolor=None,),
    )

rhomb = dict(
    motive="brick",
    length=0.8,
    height=0.2,
    length_ratio=1.,
    height_ratio=1.,
    offset_ratio=0.5,
    tilted_ratio=0.25,
    params = dict(edgecolor='black',facecolor=None,),
    )

chert = dict(
    motive="triangle",
    length=0.8/3,
    height=0.2/1.5,
    length_ratio=3.,
    height_ratio=1.5,
    offset_ratio=0.5,
    tilted_ratio=0.,
    params = dict(edgecolor='black',facecolor="white",),
    )