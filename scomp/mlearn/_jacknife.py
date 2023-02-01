import os
import sys

from matplotlib import pyplot

import numpy

from scipy.stats import norm

class jacknife():

    def __init__(self,prop,**kwargs):

        self.set_property(prop,**kwargs)