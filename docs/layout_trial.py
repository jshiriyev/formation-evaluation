from bokeh.plotting import show

from bokeh.layouts import gridplot

import lasio

import numpy as np

from lasview import depthwise as dw

file = lasio.read('digitized_data.las')

wizard = dw.Wizard(
	file,
	trail = 5,
	cycle = 4,
	depth = dict(spot=2),
	# depth = dict(values=file['DEPT'],spot=1),
	width = (60,100,150,200,250),
	height = (50,20),
	)

# print(np.min(file[0]),np.max(file[0]))

# print(wizard.trail)
# print(wizard.cycle)
# print(wizard.label.limit)
# print(wizard.label.spot)
# print(wizard.depth.limit)
# print(wizard.depth.spot)
# print(wizard.width)
# print(wizard.height)

# print(wizard.depth.limit)
# print(wizard.depth.major)
# print(wizard.depth.minor)
# print(wizard.depth.scale)
# print(wizard.depth.spot)

# grtot,grtot_lim = wizard[0](file['GR-TOT'],)

heads,bodys = dw.bokeh.boot(wizard)

# print(file.keys())

# bodys[0].line(grtot,depth)

grid = gridplot([heads,bodys],toolbar_location=None)

show(grid)