import sys

sys.path.append(r'C:\\Users\\3876yl\\Documents\\pphys')

# from bokeh.plotting import figure, output_file, show

from matplotlib import gridspec
from matplotlib import pyplot

import mpld3

import plotly.graph_objects as go

from pphys.lasview.depthview.layout._layout import Layout

layout = Layout()

# print(layout[0].cycle)

# print(layout.depth.cycle)



fig = go.Figure()

fig.update_layout(
    xaxis=dict(
        tickmode='linear',
        tick0=0,
        dtick=1
    ),
    yaxis=dict(
        tickmode='linear',
        tick0=0,
        dtick=1
    ),
    margin=dict(l=50, r=50, t=50, b=50),
    showlegend=True
)


fig.show()

# fig = pyplot.figure(figsize=layout.figsize)

# gspecs = gridspec.GridSpec(
# 	nrows = 2,
# 	ncols = layout.ntrail,
# 	figure = fig,
# 	width_ratios = [w/sum(layout.width) for w in layout.width],
# 	height_ratios = (layout.height[0]*layout.ncurve,layout.height[1]*layout.depth.length),
# 	)

for index in range(layout.ntrail):

	continue

	head = fig.add_subplot(gspecs[0,index])
	body = fig.add_subplot(gspecs[1,index])

	head.set_ylim(layout.label.limit)
	body.set_ylim(layout.depth.limit)

	head.set_xlim(layout[index].limit)
	body.set_xlim(layout[index].limit)

# gspecs.tight_layout(fig)

# mpld3.show()

# pyplot.show()