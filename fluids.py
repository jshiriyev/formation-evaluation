import numpy

class phase():

	def __init__(self):

		pass

class component():

	def __init__(self):

		pass

class mixture():

    def __init__(self,number):

        self.number = number

        self.itemnames = []
        self.molarweight = []
        self.density = []
        self.compressibility = []
        self.viscosity = []
        self.fvf = []

    def set_names(self,*args):

        for arg in args:
            self.itemnames.append(arg)

    def set_molarweight(self,*args):

        for arg in args:
            self.molarweight.append(arg)

    def set_density(self,density1,*args):

        self.density = [density1,]

        for arg in args:
            self.density.append(arg)

    def set_compressibility(self,*args):

        for arg in args:
            self.compressibility.append(arg)

    def set_viscosity(self,*args):

        for arg in args:
            self.viscosity.append(arg)

    def set_fvf(self,*args):

        for arg in args:
            self.fvf.append(arg)