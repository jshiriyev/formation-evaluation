import sys

sys.path.append(r'C:\\Users\\3876yl\\Documents\\pphys')

from bokeh.plotting import figure, show
from bokeh.layouts import gridplot

from bokeh.models import ColumnDataSource
from bokeh.models import Range1d
from bokeh.models import LinearAxis

from pphys.lasview.depthview.layout._layout import Layout

layout = Layout(ntrail=4,width=(100,250),height=(50,50))

depths = [100, 200, 300, 400, 500]  # Depths in reverse order
curve1 = [0.1, 0.2, 0.3, 0.4, 0.5]  # Curve values for trail 1
curve2 = [0.2, 0.3, 0.4, 0.5, 0.6]  # Curve values for trail 2

# source = ColumnDataSource(data=dict(depths=depths,curve1=curve1,curve2=curve2,))

heads = []
bodys = []

for index in range(layout.ntrail):

	width  = layout.width[index]

	hheight = layout.height[0]*layout.ncurve
	bheight = layout.height[1]*layout.depth.length

	head = figure(width=width,height=int(hheight))
	body = figure(width=width,height=int(bheight))

	head.add_layout(LinearAxis(major_label_text_alpha=0),'right')
	head.add_layout(LinearAxis(major_label_text_alpha=0),'above')

	body.add_layout(LinearAxis(major_label_text_alpha=0),'right')
	body.add_layout(LinearAxis(major_label_text_alpha=0),'above')

	head.y_range = Range1d(*layout.label.limit)
	body.y_range = Range1d(*layout.depth.limit)

	head.x_range = Range1d(*layout[index].limit)
	body.x_range = Range1d(*layout[index].limit)

	head.xaxis.major_label_text_font_size = '0pt'
	head.yaxis.major_label_text_font_size = '0pt'

	body.xaxis.major_label_text_font_size = '0pt'
	body.yaxis.major_label_text_font_size = '0pt'

	head.xaxis.major_tick_in = 0
	head.yaxis.major_tick_in = 0
	body.xaxis.major_tick_in = 0
	body.yaxis.major_tick_in = 0

	head.xaxis.major_tick_out = 0
	head.yaxis.major_tick_out = 0
	body.xaxis.major_tick_out = 0
	body.yaxis.major_tick_out = 0

	head.xaxis.minor_tick_in = 0
	head.yaxis.minor_tick_in = 0
	body.xaxis.minor_tick_in = 0
	body.yaxis.minor_tick_in = 0

	head.xaxis.minor_tick_out = 0
	head.yaxis.minor_tick_out = 0
	body.xaxis.minor_tick_out = 0
	body.yaxis.minor_tick_out = 0

	head.min_border_left = 0
	if index != layout.ntrail-1:
		head.min_border_right = 0
	head.min_border_top = 0
	head.min_border_bottom = 0

	body.min_border_left = 0
	if index != layout.ntrail-1:
		body.min_border_right = 0
	body.min_border_top = 0
	# body.min_border_bottom = 0

	head.line((0,20),(10,10))
	head.line((0,20),(20,20))

	heads.append(head)
	bodys.append(body)

grid = gridplot([heads,bodys],toolbar_location=None)

# p1.line(curve1, depths, line_width=2)
# p2.line(depths, depths, line_width=2)
# p3.line(curve2, depths, line_width=2)

show(grid)