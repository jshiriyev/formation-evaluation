from ._head import Head
from ._body import Body

class Track():

	def __init__(self,head:Head,body:Body):

		self._head = head
		self._body = body

	@property
	def head(self):
		return self._head
	
	@property
	def body(self):
		return self._body
	