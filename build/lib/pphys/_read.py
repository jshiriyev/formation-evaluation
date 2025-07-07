from ._lasio import LASIO

def read(file_ref,**kwargs):
	"""Read LAS files from a directory
	
	Parameters:
	----------
	file_ref  : Directory containing LAS files.

	Returns:
	-------
	LASIO: A class inherited from lasio.LASFile with added methods.

	"""
	return LASIO(file_ref,**kwargs)