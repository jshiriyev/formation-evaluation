"""
Utility Functions to digitialize Well Log Figures
provided by Yildiz Karakece 2011.
"""
import os

import numpy as np

from scipy.interpolate import make_smoothing_spline

def resample(depth, array, udepth, **kwargs):
	"""Returns Curve Values Ready To put into LasFile.

	udepth 		: Uniformly spaced depth values where to
				interpolate csv output
				
	"""
	indices = np.argsort(depth)

	x = depth[indices]
	y = array[indices]

	if len(kwargs)==0:
		return np.interp(udepth,x,y)

	unique_x = np.unique(x)

	if len(x) != len(unique_x):

		print(f"Duplicate depth values found.")

		x, indices = np.unique(x, return_index=True)

		y = y[indices]  # Retain only corresponding y value

	return make_smoothing_spline(x,y,**kwargs)(udepth)


	