import lasio

from .layout._label import Label
from .layout._depth import Depth
from .layout._xaxis import Xaxis

from .layout._layout import Layout

from .layout._datum import Datum

class Wizard(Layout):

	def __init__(self,lasfile:lasio.LASFile,**kwargs):

		self._lasfile = lasfile

		super().__init__(**kwargs)

	@property
	def lasfile(self):
		return self._lasfile

	@property
	def depth(self):
		return self._depth
	
	@depth.setter
	def depth(self,value:dict):

		power = -1 if value.get("power") is None else value.pop("power")

		if value.get("limit") is None:
			value["limit"] = Datum(self.lasfile[0],power=power).limit

		self._depth = Depth(**value)

if __name__ == "__main__":

	layout = Layout(trails=5,curves=3,width=(2,),label_loc="top")

	print(layout.width)

	print(layout.head.curves)
	print(layout.head.height)
	print(layout.body.height)