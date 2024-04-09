import sys

sys.path.append(r'C:\\Users\\3876yl\\Documents\\pphys')

from bokeh.plotting import figure, show
from bokeh.layouts import gridplot
from bokeh.models import ColumnDataSource

from bokeh.models import Range1d

from pphys.lasview.depthview.layout._layout import Layout

layout = Layout(width=(200,400),height=(100,50))

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

	head.y_range = Range1d(*layout.label.limit)
	body.y_range = Range1d(*layout.depth.limit)

	head.x_range = Range1d(*layout[index].limit)
	body.x_range = Range1d(*layout[index].limit)

	head.xaxis.major_label_text_font_size = '0pt'
	head.yaxis.major_label_text_font_size = '0pt'

	body.xaxis.major_label_text_font_size = '0pt'
	body.yaxis.major_label_text_font_size = '0pt'

	head.xaxis.major_tick_line_color = None
	head.xaxis.minor_tick_line_color = None

	head.yaxis.major_tick_line_color = None
	head.yaxis.minor_tick_line_color = None

	body.xaxis.major_tick_line_color = None
	body.xaxis.minor_tick_line_color = None

	body.yaxis.major_tick_line_color = None
	body.yaxis.minor_tick_line_color = None

	head.min_border_left = 0
	head.min_border_right = 0
	head.min_border_top = 0
	head.min_border_bottom = 0

	body.min_border_left = 0
	body.min_border_right = 0
	body.min_border_top = 0
	body.min_border_bottom = 0

	heads.append(head)
	bodys.append(body)

grid = gridplot([heads,bodys])

# p1.line(curve1, depths, line_width=2)
# p2.line(depths, depths, line_width=2)
# p3.line(curve2, depths, line_width=2)

show(grid)