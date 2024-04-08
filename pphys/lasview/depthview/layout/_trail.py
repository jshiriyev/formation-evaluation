from ._box import Box

class Trail():

	def __init__(self,head:Box=None,body:Box=None):

		object.__setattr__(self,"head",
			Box() if head is None else head)

		object.__setattr__(self,"body",
			Box() if body is None else body)

	def __setattr__(self,key,box:Box):

		if key=="head":
			object.__setattr__(self,"head",box)
		elif key=="body":
			object.__setattr__(self,"body",box)
		else:
			raise Warning("head or body can be assigned only!")

if __name__ == "__main__":

	pass

	# a = Trail()
	
	# print(a.head)

	# a.apple = 7

	# print(a.head)