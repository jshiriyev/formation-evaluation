"""The arrangement of a one-page log: tracks, header rows and depth window."""

from dataclasses import replace

from ._depth import DepthDict
from ._label import LabelDict
from ._xaxis import XAxisDict


class Layout:
	"""The arrangement of a one-page log, before anything is drawn.

	It holds one XAxisDict per track, the LabelDict of the header rows and
	the DepthDict of the depth window, and sizes the tracks from them.
	"""

	def __init__(
		self,
		ntrail : int = 3,
		ncycle : int = 3,
		label : dict | LabelDict | None = None,
		depth : dict | DepthDict | None = None,
		widths : tuple[float, ...] | None = None,
		heights : tuple[float, float] | None = None
		):
		"""It sets elements for different trails in the axes:

		ntrail 	: number of trails (tracks) including the depth trails.
		ncycle 	: number of header rows, the most curves a trail lists.

		label   : the header rows, a LabelDict or its keywords. Its limit
				defaults to (0, ncycle*major), one row per cycle.
		depth 	: the depth window and depth trails, a DepthDict or its
				keywords.

		widths 	: widths of the trails: one value for all of them, two for
				(depth trails, other trails), or one per trail. Defaults to
				(2, 4).

		heights : (height of a header row, height per depth unit). Defaults
				to (50, 20).

		Set each trail's x axis with ``set(index, limit=, scale=, ...)``.
		"""
		if int(ntrail)<1 or int(ncycle)<1:
			raise ValueError("ntrail and ncycle must be at least 1.")

		self._ntrail = int(ntrail)
		self._ncycle = int(ncycle)

		self._depth = depth if isinstance(depth,DepthDict) else DepthDict(**(depth or {}))

		for spot in self._depth.spot:
			if not 0<=spot<self._ntrail:
				raise ValueError(f"Depth trail {spot} is outside the {self._ntrail} trails.")

		label = label if isinstance(label,LabelDict) else LabelDict(**(label or {}))

		if label.limit is None:
			label = replace(label,limit=(0.,self._ncycle*label.major))

		self._label = label

		self._xaxes = [XAxisDict() for _ in range(self._ntrail)]

		self.widths  = widths
		self.heights = heights

	@property
	def ntrail(self) -> int:
		"""Return the number of trails."""
		return self._ntrail

	def __len__(self):
		return self._ntrail

	@property
	def ncycle(self) -> int:
		"""Return the number of header rows."""
		return self._ncycle

	@property
	def shape(self):
		return (self.ntrail,self.ncycle)

	def set(self,index:int,**kwargs):
		"""Set the x axis of a trail from XAxisDict keywords."""
		self[index] = XAxisDict(**kwargs)

	def __setitem__(self,index:int,xaxis:XAxisDict):
		if not isinstance(xaxis,XAxisDict):
			raise TypeError(f"A trail takes an XAxisDict, not {type(xaxis).__name__}.")

		self._xaxes[index] = xaxis

	def __getitem__(self,index:int) -> XAxisDict:
		return self._xaxes[index]

	@property
	def widths(self) -> tuple[float, ...]:
		"""Return the width of each trail."""
		return self._widths

	@widths.setter
	def widths(self,value:tuple[float, ...] | None):

		value = (2.,4.) if value is None else tuple(value)

		if len(value)==self.ntrail:
			widths = value

		elif len(value)==1:
			widths = value*self.ntrail

		elif len(value)==2:
			widths = [value[0] if index in self._depth.spot else value[1] for index in range(self.ntrail)]

		else:
			raise ValueError(f"widths takes 1, 2 or {self.ntrail} values, not {len(value)}.")

		if min(widths)<=0:
			raise ValueError("widths must be positive.")

		self._widths = tuple(float(width) for width in widths)

	@property
	def heights(self) -> tuple[float, float]:
		"""Return (height of a header row, height per depth unit)."""
		return self._heights

	@heights.setter
	def heights(self,value:tuple[float, float] | None):

		value = (50.,20.) if value is None else tuple(value)

		if len(value)!=2 or min(value)<=0:
			raise ValueError(f"heights takes two positive values, not {value!r}.")

		self._heights = (float(value[0]),float(value[1]))

	@property
	def height_ratios(self) -> tuple[float, ...]:
		"""Return the heights of the header and trail rows, in figure order."""
		head = self._heights[0]*self.ncycle
		body = self._heights[1]*self._depth.length

		if self._label.spot=="top":
			return (head,body)

		if self._label.spot=="bottom":
			return (body,head)

		return (body,)

	@property
	def size(self):
		"""Return the (width, height) of the layout in its own units."""
		return (sum(self.widths),sum(self.height_ratios))
