from ._lasio import LASIO

def read(file_ref,**kwargs):

	return LASIO(file_ref,**kwargs)