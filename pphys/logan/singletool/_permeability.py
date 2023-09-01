class nmr():

    def dollmodel():

        pass

def set_perm(self,PHI,method=None):

    PHIE = self[PHI].vals

    PERM = 50*((1-0.13)**2)/(0.13**3)*(PHIE**3)/((1-PHIE)**2)

    depth = self.lasfile.depth

    info = 'Permeability calculated from effective porosity.'

    self.add_curve(vals=PERM,depth=depth,head='PERM',unit='mD',info=info)