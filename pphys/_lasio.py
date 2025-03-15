import logging

import lasio
import numpy

class LasIO():

	def __init__(self,file_ref,**kwargs):

		logging.info("Attempting to read las file by using lasio module.")

		try:
			self._las = lasio.read(file_ref,**kwargs)
		except Exception as e:
			logging.error(f"Error reading LAS file: {e}")
			self._las = lasio.LASFile()
		else:
			logging.info(f"LAS file '{file_ref}' loaded successfully.")
	
	@property
	def las(self):
		"""Getter for the LAS file object."""
		return self._las

	def __getattr__(self,key):
		"""Directing attribute access to self.las."""
		return getattr(self.las,key)

	def __getitem__(self,key):
		"""Directing item access to self.las."""
		return getitem(self.las,key)

	def mask(self,dmin:float=None,dmax:float=None):
		"""
		Selects a depth interval and returns a boolean array.

		Parameters:
        dmin (float): Minimum depth of the interval.
        dmax (float): Maximum depth of the interval.

		Returns:
        np.ndarray: Boolean array where True indicates depths within the interval.
		"""
		dmin = self.las.index.min() if dmin is None else dmin
		dmax = self.las.index.max() if dmax is None else dmax

		return numpy.logical_and(self.las.index>=dmin,self.las.index<=dmax)

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

		return self.las.df[mask] if key is None else self.las[key].values[mask]

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
		return numpy.interp(depths,self.las.index,self.las[key])

	def copy(self):
		"""Create a new LAS object with the cropped data"""
	    cropped_las = lasio.LASFile()

	    cropped_las.index = cropped_data.index  # Set the new depth index

	    for curve in self.las.curves:
	        if curve.mnemonic in cropped_data.columns:
	            cropped_las.add_curve(
	                curve.mnemonic,
	                cropped_data[curve.mnemonic].values,
	                unit=curve.unit,
	                descr=curve.descr,
	            )

	    return cropped_las

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

	pass