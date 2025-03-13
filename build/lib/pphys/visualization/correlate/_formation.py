class Formation():
	"""A class to store and utilize formation tops across the pphys."""

	def __init__(self,**kwargs):
		"""Initializes the Formation with named top values."""

		keys,tops = [],[]

		for name,vals in kwargs.items():
			keys.append(name)
			tops.append(vals)

		sorted_pairs = sorted(zip(tops,keys))

		self._tops,self._keys = zip(*sorted_pairs)

	def index(self,key):
		"""Returns the index of formation based on its name."""
		return self.keys.index(key)

	def __getitem__(self,key):
		"""Returns the list of formation tops based on formation name."""
		return self.tops[self.index(key)]

	def limit(self,key):
		"""Returns the list of formation tops and bottoms based on formation name."""
		return self.tops[self.index(key)], self.tops[self.index(key)+1]

	@property
	def keys(self):
		return self._keys

	@property
	def tops(self):
		return self._tops