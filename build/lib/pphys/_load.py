import pathlib
import pickle

from ._lasio import LASIO

def load(source_path:str,cache_path:str,**kwargs) -> dict:
	"""Load LAS files from a directory, using a cache to avoid redundant processing.
	
	Parameters:
	----------
	source_path  : Directory containing LAS files.
	cache_path 	 : Directory where cached files will be stored.

	Returns:
	-------
	dict: A dictionary with filenames (without extension) as keys and LAS data as values.
	
	"""

	# Ensure cache directory exists
	pathlib.Path(cache_path).mkdir(parents=True, exist_ok=True)

	las_files = {}  # Dictionary to store LAS data

	# Loop through all .las files in the directory
	for las_file in pathlib.Path(source_path).glob("*.las"):
		cache_file = pathlib.Path(cache_path) / f"{las_file.stem}.pkl"  # Cache filename

		# If a cached version exists, load it
		if cache_file.exists():
			with open(cache_file, "rb") as f:
				las_data = pickle.load(f)
		else:
			# Otherwise, read and cache the LAS file
			las_data = LASIO(str(las_file),**kwargs)
			with open(cache_file, "wb") as f:
				pickle.dump(las_data,f)

		# Store in dictionary with filename as key
		las_files[las_file.stem] = las_data

	return las_files  # Dictionary of {filename: LASFile}