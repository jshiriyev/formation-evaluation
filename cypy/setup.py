import setuptools
from distutils.core import setup
from Cython.Build import cythonize

setup(ext_modules=cythonize('vectorcy.pyx',
	compiler_directives={'language_level' : "3"}))