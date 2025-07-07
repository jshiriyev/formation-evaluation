import os
import pathlib
import pickle

from ._lasio import LASIO

def load(path:str,cache:str) -> dict:
	"""Load LAS files from a directory, using a cache to avoid redundant processing.
	
	Parameters:
	----------
	path  : Directory containing LAS files.
	cache : Directory where cached files will be stored.

	Returns:
	-------
	dict: A dictionary with filenames (without extension) as keys and LAS data as values.
	
	"""

	# Ensure cache directory exists
	# os.makedirs(cache,exist_ok=True)
	pathlib.Path(cache).mkdir(parents=True, exist_ok=True)

	las_files = {}  # Dictionary to store LAS data

	# Loop through all .las files in the directory
	for las_file in pathlib.Path(path).glob("*.las"):
		cache_file = pathlib.Path(cache) / f"{las_file.stem}.pkl"  # Cache filename

		# If a cached version exists, load it
		if cache_file.exists():
			with open(cache_file, "rb") as f:
				las_data = pickle.load(f)
		else:
			# Otherwise, read and cache the LAS file
			las_data = LASIO(str(las_file))
			with open(cache_file, "wb") as f:
				pickle.dump(las_data,f)

		# Store in dictionary with filename as key
		las_files[las_file.stem] = las_data

	return las_files  # Dictionary of {filename: LASFile}