import pathlib
import pickle

from ._lasio import LASIO

def read(file_path,cache_path:str=None,**kwargs):
	"""Read LAS files with optional caching using pickle.
	
	Parameters:
	----------
	file_path: str
        Path to the LAS file.

    cache_path: str, optional
        Directory to store or load the cached `.pkl` file.

	Returns:
	-------
	LASIO:
		A class inherited from lasio.LASFile with added methods.

	"""
	cache_file = f"{pathlib.Path(file_path).stem}.pkl"

	if cache_path is not None:
		cache_file = pathlib.Path(cache_path) / cache_file

	if cache_file.exists():
		with open(cache_file, "rb") as f:
			las_data = pickle.load(f)
	else:
		las_data = LASIO(str(file_path),**kwargs)

		with open(cache_file, "wb") as f:
			pickle.dump(las_data,f)

	return las_data