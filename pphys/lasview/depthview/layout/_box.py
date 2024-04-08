from ._axis import Axis

class Box():

	def __init__(self,xaxis:Axis=None,yaxis:Axis=None):

		object.__setattr__(self,"xaxis",
			Axis() if xaxis is None else xaxis)

		object.__setattr__(self,"yaxis",
			Axis() if yaxis is None else yaxis)

	def __setattr__(self,key,axis:Axis):

		if key=="xaxis":
			object.__setattr__(self,"xaxis",box)
		elif key=="yaxis":
			object.__setattr__(self,"yaxis",box)
		else:
			raise Warning("xaxis or yaxis can be assigned only!")

	def set_xaxis(self,**kwargs):

		object.__setattr__(self,"xaxis",Axis(**kwargs))

	def set_yaxis(self,**kwargs):

		object.__setattr__(self,"yaxis",Axis(**kwargs))