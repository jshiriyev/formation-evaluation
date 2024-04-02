class Axes():

	def __init__(self,ncols=None,nrows=None,depthloc=None,labelloc="top",depth=6,label=6,width=15,height=70):
	    """
	    It sets grid number for different elements in the axes:

	    ncols       : number of column axis including depth axis in the figure, integer
	    nrows       : number of curves in the axes, integer, nrows*label defines
	                  grid number in the height of labels
	    depthloc    : location of depth axis, integer
	    labelloc    : location of label axis, top, bottom or None
	    depth       : grid number in the width of depth xaxis, integer
	    label       : grid number in the height of individual label, integer
	    width       : grid number in the width of curve individual xaxis, integer
	    height      : grid number in the height of curve yaxis, integer
	    """

	    if ncols is None:
	        ncols = self.columns+1

	    if nrows is None:
	        nrows = self.rows

	    self.axes['ncols'] = ncols
	    self.axes['nrows'] = nrows

	    if depthloc is None:
	        depthloc = 0 if ncols<3 else 1

	    self.axes['depthloc'] = depthloc
	    self.axes['labelloc'] = str(labelloc).lower()

	    self.axes['depth'] = depth
	    self.axes['label'] = label
	    self.axes['width'] = width
	    self.axes['height'] = height

	    self.axes['size'] = (depth+ncols*width,nrows*label+height)

	    if self.axes['labelloc'] == "none":
	        self.axes['naxes_percolumn'] = 1
	        self.axes['label_indices'] = slice(0)
	        self.axes['curve_indices'] = slice(ncols)
	    elif self.axes['labelloc'] == "top":
	        self.axes['naxes_percolumn'] = 2
	        self.axes['label_indices'] = slice(0,ncols*2,2)
	        self.axes['curve_indices'] = slice(1,ncols*2,2)
	    elif self.axes['labelloc'] == "bottom":
	        self.axes['naxes_percolumn'] = 2
	        self.axes['label_indices'] = slice(0,ncols*2,2)
	        self.axes['curve_indices'] = slice(1,ncols*2,2)
	    else:
	        raise ValueError(f"{labelloc} has not been defined! options: {{top,bottom}}")

	    width_ratio = [width]*self.axes["ncols"]
	    width_ratio[depthloc] = depth

	    # width_ratio[3] = 30

	    # print(width_ratio)

	    self.axes["width_ratio"] = tuple(width_ratio)

	    if self.axes['labelloc'] == 'none':
	        height_ratio = [height]
	    elif self.axes['labelloc'] == 'top':
	        height_ratio = [nrows*label,height]
	    elif self.axes['labelloc'] == 'bottom':
	        height_ratio = [height,nrows*label]

	    self.axes["height_ratio"] = tuple(height_ratio)

	    self.axes['xaxis'] = [{} for _ in range(ncols)]

	    for index in range(self.axes['ncols']):
	        self.set_xaxis(index)