import numpy

class neutron():

    def __init__(self,values,depths=None,phinfluid=1.0):
        """Initializes neutron porosity values and depths for porosity calculations.
        If depths values are provided, they must be the same size as values."""
        self.values = values
        self.depths = depths

        self.phinfluid = phinfluid

    def phin(self):
        return self.values

    def phincorr(self,phin,vshale,phinsh=0.35):
        """Calculates shale corrected neutron porosity based on shale volume (vshale) and
        phinsh (neutron porosity at shale).
        """
        phin_corrected = phin-vshale*phinsh

        phin_corrected[phin_corrected>1] = 1
        phin_corrected[phin_corrected<0] = 0

        return phin_corrected

    def _gamma_capture_total(self,phi_clean,phi_shale,ngl_clean=None,ngl_shale=None):
        """The porosity based on gamma detection:
        
        phi_clean    :  porosity in the clean formation
        phi_shale    :  porosity in the adjacent shale

        ngl_clean    :  NGL reading in the clean formation
        ngl_shale    :  NGL reading in the adjacent shale
        
        """

        if ngl_clean is None:
            ngl_clean = self.NGL.min()

        if ngl_shale is None:
            ngl_shale = self.NGL.max()

        normalized = (self.NGL.vals-ngl_clean)/(ngl_shale-ngl_clean)

        normalized[normalized<=0] = 0
        normalized[normalized>=1] = 1

        PHIT = phi_clean+(phi_shale-phi_clean)*normalized

        info = 'Total porosity calculated from neutron-gamma-log.'

        return LasCurve(
            depth = self.NGL.depth,
            vals = PHIT,
            head = 'PHIT',
            unit = '-',
            info = info)

    def _gamma_capture_effective(self,phi_clean,phi_shale,**kwargs):
        """
        shale_volume :  it is required for the calculation of effective porosity,
                        and it can be calculated from etiher GR or SP logs.
        """

        PHIT = self._gamma_capture_total(phi_clean,phi_shale,**kwargs)

        PHIE = PHIT.vals-self.VSH.vals*phi_shale

        info = 'Effective porosity calculated from neutron-gamma-log.'

        return LasCurve(
            depth = self.NGL.depth,
            vals = PHIE,
            head = 'PHIE',
            unit = '-',
            info = info)

    def _neutron_count(self,a,b):
        """The porosity based on the neutron count is given by:
        
        nnl = a-b*log(phi)
        
        curve   :  neutron-neutron-logging curve, the slow neutrons counted

        a       :  empirical constants determined by appropriate calibration
        b       :  empirical constants determined by appropriate calibration

        phi     :  porosity

        """

        porosity = {}

        total = 10**((a-curve.vals)/b)

        return total

class density():

    def __init__(self,values,depths=None,rhofluid=1.0):
        """Initializes bulk density values and depths for porosity calculations.
        If depths values are provided, they must be the same size as values."""
        self.values = values
        self.depths = depths

        self.rhofluid = rhofluid

    def phid(self,rhomat=2.65,rhofluid=1.0):
        """Calculates porosity based on bulk density, matrix density (rhomat), and fluid density (rhofluid)."""
        phi_density = (rhomat-self.values)/(rhomat-rhofluid)

        phi_density[phi_density>1] = 1
        phi_density[phi_density<0] = 0

        return phi_density

    def phidcorr(self,phid,vshale,phidsh=0.1):
        """Calculates shale corrected density porosity based on shale volume (vshale) and
        phidsh (density porosity at shale).
        """
        phid_corrected = phid-vshale*phidsh

        phid_corrected[phid_corrected>1] = 1
        phid_corrected[phid_corrected<0] = 0

        return phid_corrected

class sonic():

    def __init__(self,values,depths):
        """Initializes sonic transit times and depths for porosity calculations.
        If depths values are provided, they must be the same size as values."""
        self.values = values
        self.depths = depths

    def phis(self,dtmat,dtfluid,dtshale=100):
        """Calculates porosity based on transit times, matrix transit time (dtmat),
        fluid transit time (dtfluid), and (optional) adjacent shale transit time (dtshale)."""
        phi_sonic = (self.values-dtmat)/(dtfluid-dtmat)*(100/dtshale)

        phi_sonic[phi_sonic>1] = 1
        phi_sonic[phi_sonic<0] = 0

        return phi_sonic

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

class sonneu():

    def __init__(self,DT_FLUID=189,PHI_NF=1,**kwargs):

        self.DT_FLUID = DT_FLUID
        self.PHI_NF = PHI_NF

    def lithos(self):

        # porLine,
        # sonLine,
        # a_SND=+0.00,
        # a_LMS=+0.00,
        # a_DOL=-0.06,
        # b_SND=+0.90,
        # b_LMS=+0.80,
        # b_DOL=+0.84,
        # p_SND=+0.02,
        # p_LMS=+0.00,
        # p_DOL=-0.01,
        # DT_SND=55.6,
        # DT_LMS=47.5,
        # DT_DOL=43.5,
        # xmin=None,
        # ymin=None,
        # xmax=None,
        # ymax=None,
        # rotate=0

        self.fig_sncp.set_figwidth(5)
        self.fig_sncp.set_figheight(6)

        c1_SND = 10**((a_LMS-a_SND)/b_LMS)
        c1_LMS = 10**((a_LMS-a_LMS)/b_LMS)
        c1_DOL = 10**((a_LMS-a_DOL)/b_LMS)

        c2_SND = b_SND/b_LMS
        c2_LMS = b_LMS/b_LMS
        c2_DOL = b_DOL/b_LMS

        porSND = numpy.linspace(0,0.45,46)
        porLMS = numpy.linspace(0,0.45,46)
        porDOL = numpy.linspace(0,0.45,46)

        sonicSND = porSND*(DT_FLUID-DT_SND)+DT_SND
        sonicLMS = porLMS*(DT_FLUID-DT_LMS)+DT_LMS
        sonicDOL = porDOL*(DT_FLUID-DT_DOL)+DT_DOL

        porLMS_SND = c1_SND*(porSND)**c2_SND-p_SND
        porLMS_LMS = c1_LMS*(porLMS)**c2_LMS-p_LMS
        porLMS_DOL = c1_DOL*(porDOL)**c2_DOL-p_DOL

        xaxis_max = 0.5
        yaxis_max = 110

        for depth in self.depths:

            xaxis = self.get_interval(*depth[1:],idframe=porLine[0],curveID=porLine[1])
            yaxis = self.get_interval(*depth[1:],idframe=sonLine[0],curveID=sonLine[1])

            xaxis_max = max((xaxis_max,xaxis[0].max()))
            yaxis_max = max((yaxis_max,yaxis[0].max()))

            self.axis_sncp.scatter(xaxis,yaxis,s=1,label=depth[0])

        self.axis_sncp.legend(scatterpoints=10)

        self.axis_sncp.plot(porLMS_SND,sonicSND,color='blue',linewidth=0.3)
        self.axis_sncp.plot(porLMS_LMS,sonicLMS,color='blue',linewidth=0.3)
        self.axis_sncp.plot(porLMS_DOL,sonicDOL,color='blue',linewidth=0.3)

        self.axis_sncp.scatter(porLMS_SND[::5],sonicSND[::5],marker=(2,0,45),color="blue")
        self.axis_sncp.scatter(porLMS_LMS[::5],sonicLMS[::5],marker=(2,0,45),color="blue")
        self.axis_sncp.scatter(porLMS_DOL[::5],sonicDOL[::5],marker=(2,0,45),color="blue")

        self.axis_sncp.text(porLMS_SND[27],sonicSND[26],'Sandstone',rotation=rotate)
        self.axis_sncp.text(porLMS_LMS[18],sonicLMS[17],'Calcite (limestone)',rotation=rotate)
        self.axis_sncp.text(porLMS_DOL[19],sonicDOL[18],'Dolomite',rotation=rotate)

        self.axis_sncp.set_xlabel("Apparent Limestone Neutron Porosity")
        self.axis_sncp.set_ylabel("Sonic Transit Time $\\Delta$t [$\\mu$s/ft]")

        xaxis_min = -0.05 if xmin is None else xmin
        yaxis_min = +40.0 if ymin is None else ymin

        xaxis_max = xaxis_max if xmax is None else xmax
        yaxis_max = yaxis_max if ymax is None else ymax

        self.axis_sncp.set_xlim([xaxis_min,xaxis_max])
        self.axis_sncp.set_ylim([yaxis_min,yaxis_max])

        self.axis_sncp.xaxis.set_minor_locator(AutoMinorLocator(10))
        self.axis_sncp.yaxis.set_minor_locator(AutoMinorLocator(10))

        self.axis_sncp.grid(True,which="both",axis='both')

        self.fig_sncp.tight_layout()

    def litholines(self,axis):

        pass

    def ternary(self,axis):

        pass

    def lithoratio(self):

        pass

class sonden():

    def __init__(self,**kwargs):

        pass