import lasio
import numpy

class LASIO(lasio.LASFile):

	def __init__(self,file_ref,**kwargs):

		super().__init__(file_ref,**kwargs)

	def mask(self,dmin:float=None,dmax:float=None):
		"""
		Selects a depth interval and returns a boolean array.

		Parameters:
		dmin (float): Minimum depth of the interval.
		dmax (float): Maximum depth of the interval.

		Returns:
		np.ndarray: Boolean array where True indicates depths within the interval.
		"""
		dmin = self.index.min() if dmin is None else dmin
		dmax = self.index.max() if dmax is None else dmax

		return numpy.logical_and(self.index>=dmin,self.index<=dmax)

	def crop(self,dmin:float=None,dmax:float=None,key:str=None):
		"""
		Crops a LAS frame (or curve if key is provided) to include only data
		within a specified depth range.

		Parameters:
		----------
		dmin (float): Minimum depth for cropping.
		dmax (float): Maximum depth for cropping.
		key (str): Name of the curve to crop.
		
		Returns:
		-------
		numpy.ndarray or pandas.DataFrame: Cropped curve values.
		"""
		mask = self.mask(dmin,dmax)

		return self.df()[mask] if key is None else self[key].values[mask]

	def resample(self,depths:numpy.ndarray,key:str=None):
		"""
		Resample a curve's values based on new depth values.

		Parameters:
		----------
		depths (array-like): New depth values for resampling.
		key (str): Name of the curve to resample.

		Returns:
		-------
		numpy.ndarray or pandas.DataFrame: Resampled curve values.
		"""
		interp = lambda values: numpy.interp(depths,self.index,values)

		return self.df.apply(interp) if key is None else interp(self[key])

	def copy(self):
		"""Create a new LAS object with the cropped data"""
		las = lasio.LASFile()

		las.index = cropped_data.index  # Set the new depth index

		for curve in self.curves:
			if curve.mnemonic in cropped_data.columns:
				las.add_curve(
					curve.mnemonic,
					cropped_data[curve.mnemonic].values,
					unit=curve.unit,
					descr=curve.descr,
				)

		return las

	@staticmethod
	def is_valid(values:numpy.ndarray):
		return numpy.all(~numpy.isnan(values))

	@staticmethod
	def is_positive(values:numpy.ndarray):
		return numpy.all(values>=0)

	@staticmethod
	def is_sorted(values:numpy.ndarray):
		return numpy.all(values[:-1]<values[1:])

if __name__ == "__main__":

	# las = LasIO("G:\\My Drive\\Modeling Repository\\02_GeoM_Reservoir_Characterization\\Well_Data_Visualization\\NFD_correlation\\NFD_2472.las")

	# print(las.mask(1050,1060))
	# print(las.crop(1050,1060))
	pass
	# load("G:\\My Drive\\Modeling Repository\\02_GeoM_Reservoir_Characterization\\Well_Data_Visualization\\NFD_correlation",
	# 	 "G:\\My Drive\\Modeling Repository\\02_GeoM_Reservoir_Characterization\\Well_Data_Visualization\\cache")