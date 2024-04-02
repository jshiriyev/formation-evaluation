import numpy

from borepy.utils._wrappers import trim

class neuden():

    def __init__(self,phin,phid,phinsh=0.35,phidsh=0.1,NTool="CNL"):
        """Initialization of neutron-density interpretation.

        phin    : porosity calculated from neutron log
        phid    : porosity calculated from density log
        
        phinsh  : apparent neutron porosity in the shale
        phidsh  : apparent density porosity in the shale
        """

        self.phin = phin
        self.phid = phid

        self.phinsh = phinsh
        self.phidsh = phidsh

    @property
    def arithmetic(self):
        """Calculates the arithmetic mean of neutron and density logs,
        and outputs values equivalent of total porosity."""
        return (self.phin+self.phid)/2

    @property
    def geometric(self):
        """Calculates the geometric mean of neutron and density logs."""
        return numpy.sqrt(self.phin*self.phid)

    @property
    def root_mean_square(self):
        """Calculates root mean square of neutron and density logs."""
        return numpy.sqrt(self.phin**2+self.phid**2)

    @property
    def rms(self):
        """Calculates root mean square of neutron and density logs."""
        return self.root_mean_square

    def lithos(self):

        phima = f"phima_{self.NTool}"

        self.Dens["SS1"] = self.SS["type1"]["rhoma"]
        self.Neus["SS1"] = self.SS["type1"][phima]

        self.Dens["SS2"] = self.SS["type2"]["rhoma"]
        self.Neus["SS2"] = self.SS["type2"][phima]

        self.Dens["LS1"] = self.LS["type1"]["rhoma"]
        self.Neus["LS1"] = self.LS["type1"][phima]

        self.Dens["DOL1"] = self.DOL["type1"]["rhoma"]
        self.Neus["DOL1"] = self.DOL["type1"][phima]

        self.Dens["DOL2"] = self.DOL["type2"]["rhoma"]
        self.Neus["DOL2"] = self.DOL["type2"][phima]

        self.Dens["DOL3"] = self.DOL["type3"]["rhoma"]
        self.Neus["DOL3"] = self.DOL["type3"][phima]

        self.Dens["ANH1"] = self.ANH["type1"]["rhoma"]
        self.Neus["ANH1"] = self.ANH["type1"][phima]

        self.Dens["SLT1"] = self.SLT["type1"]["rhoma"]
        self.Neus["SLT1"] = self.SLT["type1"][phima]

    def lithonodes(self,axis):

        DENSS  = [self.Dens["SS2"]] #self.Dens["SS1"],
        NEUSS  = [self.Neus["SS2"]] #self.Neus["SS1"],

        DENLS  = [self.Dens["LS1"]]
        NEULS  = [self.Neus["LS1"]]

        DENDOL = [self.Dens["DOL3"]] #self.Dens["DOL1"],self.Dens["DOL2"],
        NEUDOL = [self.Neus["DOL3"]] #self.Neus["DOL1"],self.Neus["DOL2"],

        DENANH = [self.Dens["ANH1"]]
        NEUANH = [self.Neus["ANH1"]]

        DENSLT = [self.Dens["SLT1"]]
        NEUSLT = [self.Neus["SLT1"]]

        axis.plot(NEUSS,DENSS,label=self.SS["lithology"],
            linestyle="None",
            marker=self.SS["marker"],
            markerfacecolor=self.SS["markercolor"],
            markeredgecolor=self.SS["markercolor"])

        axis.plot(NEULS,DENLS,label=self.LS["lithology"],
            linestyle="None",
            marker=self.LS["marker"],
            markerfacecolor=self.LS["markercolor"],
            markeredgecolor=self.LS["markercolor"])

        axis.plot(NEUDOL,DENDOL,label=self.DOL["lithology"],
            linestyle="None",
            marker=self.DOL["marker"],
            markerfacecolor=self.DOL["markercolor"],
            markeredgecolor=self.DOL["markercolor"])

        axis.plot(NEUANH,DENANH,label=self.ANH["lithology"],
            linestyle="None",
            marker=self.ANH["marker"],
            markerfacecolor=self.ANH["markercolor"],
            markeredgecolor=self.ANH["markercolor"])

        axis.plot(NEUSLT,DENSLT,label=self.SLT["lithology"],
            linestyle="None",
            marker=self.SLT["marker"],
            markerfacecolor=self.SLT["markercolor"],
            markeredgecolor=self.SLT["markercolor"])

        axis.set_xlabel(f"PHI-{self.NTool}, Apparent Limestone Porosity")
        axis.set_ylabel("RHOB Bulk Density, g/cm3")

        axis.legend(loc="upper center",ncol=3,bbox_to_anchor=(0.5,1.15))

        axis.set_xlim((-0.05,0.45))
        axis.set_ylim((3.0,1.9))

        xmajor_ticks = numpy.arange(-0.00,0.45,0.05)
        xminor_ticks = numpy.arange(-0.05,0.45,0.01)

        ymajor_ticks = numpy.arange(1.9,3.01,0.1)
        yminor_ticks = numpy.arange(1.9,3.01,0.02)

        axis.set_xticks(xmajor_ticks,minor=False)
        axis.set_xticks(xminor_ticks,minor=True)

        axis.set_yticks(ymajor_ticks,minor=False)
        axis.set_yticks(yminor_ticks,minor=True)

        axis.grid(which='both')

        axis.grid(which='minor',alpha=0.2)
        axis.grid(which='major',alpha=0.5)

        return axis

    def litholines(self,axis):

        a_SS = +0.00
        a_LS = +0.00
        a_DOL = 0.10

        b_SS = +0.90
        b_LS = +0.80
        b_DOL = +0.57

        c1_SS = 10**((a_LS-a_SS)/b_LS)
        c1_LS = 10**((a_LS-a_LS)/b_LS)
        c1_DOL = 10**((a_LS-a_DOL)/b_LS)

        c2_SS = b_SS/b_LS
        c2_LS = b_LS/b_LS
        c2_DOL = b_DOL/b_LS

        porosity = numpy.linspace(0,0.45,100)

        DENSS = self.Dens["SS2"]-porosity*(self.Dens["SS2"]-self.rhof)
        NEUSS = c1_SS*(porosity)**c2_SS+self.Neus["SS2"]

        DENLS = self.Dens["LS1"]-porosity*(self.Dens["LS1"]-self.rhof)
        NEULS = c1_LS*(porosity)**c2_LS+self.Neus["LS1"]

        DENDOL = self.Dens["DOL3"]-porosity*(self.Dens["DOL3"]-self.rhof)
        NEUDOL = c1_DOL*(porosity)**c2_DOL+self.Neus["DOL3"]

        axis.plot(NEUSS,DENSS,color='black',linewidth=0.3)
        axis.plot(NEULS,DENLS,color='black',linewidth=0.3)
        axis.plot(NEUDOL,DENDOL,color='black',linewidth=0.3)

    def terniary(self):

        pass

    def lithoratio(self):

        pass