from matplotlib import colors as mcolors
from matplotlib import gridspec
from matplotlib import pyplot
from matplotlib import transforms

from matplotlib.backend_bases import MouseButton

from matplotlib.patches import Rectangle

from matplotlib.ticker import AutoMinorLocator
from matplotlib.ticker import LogFormatter
from matplotlib.ticker import LogFormatterExponent
from matplotlib.ticker import LogFormatterMathtext
from matplotlib.ticker import LogLocator
from matplotlib.ticker import MultipleLocator
from matplotlib.ticker import NullLocator
from matplotlib.ticker import ScalarFormatter

import numpy

if __name__ == "__main__":
	import dirsetup

# TOOL INTERPRETATION

class gammaray():

    def __init__(self,values,depths=None):

        self.values = values
        self.depths = depths

    def get_unknownthickness(self):

        node_top = numpy.roll(self.depths,1)
        node_bottom = numpy.roll(self.depths,-1)

        thickness = (node_bottom-node_top)/2

        thickness[0] = (self.depths[1]-self.depths[0])/2
        thickness[-1] = (self.depths[-1]-self.depths[-2])/2

        return numpy.sum(thickness[numpy.isnan(self.values)])

    def get_shaleindex(self,grmin=None,grmax=None):

        if grmin is None:
            grmin = numpy.nanmin(self.values)

        if grmax is None:
            grmax = numpy.nanmax(self.values)

        return (self.values-grmin)/(grmax-grmin)

    def get_shalevolume(self,model="linear",factor=None,grmin=None,grmax=None):

        if grmin is None:
            grmin = numpy.nanmin(self.values)

        if grmax is None:
            grmax = numpy.nanmax(self.values)

        index = (self.values-grmin)/(grmax-grmin)

        if model == "linear":
            volume = index
        elif factor is None:
            volume = getattr(self,f"_{model}")(index)
        else:
            volume = getattr(self,f"_{model}")(index,factor=factor)

        return volume

    def get_cut(self,percent=40,model="linear",factor=None,grmin=None,grmax=None):

        if model == "linear":
            index = percent/100
        elif factor is None:
            index = getattr(self,f"_{model}")(None,volume=percent/100)
        else:
            index = getattr(self,f"_{model}")(None,volume=percent/100,factor=factor)

        if grmin is None:
            grmin = numpy.nanmin(self.values)

        if grmax is None:
            grmax = numpy.nanmax(self.values)

        return index*(grmax-grmin)+grmin

    def get_netthickness(self,percent,**kwargs):

        grcut = self.get_cut(percent,**kwargs)

        node_top = numpy.roll(self.depths,1)
        node_bottom = numpy.roll(self.depths,-1)

        thickness = (node_bottom-node_top)/2

        thickness[0] = (self.depths[1]-self.depths[0])/2
        thickness[-1] = (self.depths[-1]-self.depths[-2])/2

        return numpy.sum(thickness[self.values<grcut])

    def get_netgrossratio(self,percent,**kwargs):

        return self.get_netthickness(percent,**kwargs)/self.grossthickness

    def spectral(self,axis):

        pass

    @property
    def grossthickness(self):
        return self.depths.max()-self.depths.min()

    @staticmethod
    def _larionov_oldrocks(index,volume=None):
        if volume is None:
            return 0.33*(2**(2*index)-1)
        elif index is None:
            return numpy.log2(volume/0.33+1)/2

    @staticmethod
    def _clavier(index,volume=None):
        if volume is None:
            return 1.7-numpy.sqrt(3.38-(0.7+index)**2)
        elif index is None:
            return numpy.sqrt(3.38-(1.7-volume)**2)-0.7

    @staticmethod
    def _bateman(index,volume=None,factor=1.2):
        if volume is None:
            return index**(index+factor)
        elif index is None:
            return #could not calculate inverse yet

    @staticmethod
    def _stieber(index,volume=None,factor=3):
        if volume is None:
            return index/(index+factor*(1-index))
        elif index is None:
            return volume*factor/(1+volume*(factor-1))

    @staticmethod
    def _larionov_tertiary(index,volume=None):
        if volume is None:
            return 0.083*(2**(3.7*index)-1)
        elif index is None:
            return numpy.log2(volume/0.083+1)/3.7

class density():

    def __init__(self,values,depths=None):

        self.values = values
        self.depths = depths

    def get_porosity(self):

        pass

    def set_denphe(self,axis):

        pass

class neutron():

    def __init__(self,values,depths=None):

        self.values = values
        self.depths = depths

    def get_porosity(self):

        pass

class sonic():

    def __init__(self,values,depths=None):

        self.values = values
        self.depths = depths

    def get_porosity(self):

        pass

class spotential():

    def __init__(self,values,depths,**kwargs):

        self.values = values
        self.depths = depths

        self.set_temps(**kwargs)

    def set_temps(self,temps=None,tempmax=None,depthmax=None,tempsurf=None,tempgrad=1.75):
        """Worldwide average geothermal gradients are from 24 to 41°C/km (1.3-2.2°F/100 ft),
        with extremes outside this range"""

        if temps is None:

            if depthmax is None:
                depthmax = numpy.nanmax(self.depths)

            if tempmax is None and tempsurf is None:
                tempsurf,tempmax = 60,60+tempgrad*depthmax/100
            elif tempmax is None and tempsurf is not None:
                tempmax = tempsurf+tempgrad*depthmax/100
            elif tempmax is not None and tempsurf is None:
                tempsurf = tempmax-tempgrad*depthmax/100
            else:
                tempgrad = (tempmax-tempsurf)/depthmax*100

            self.tempsurf = tempsurf
            self.tempgrad = tempgrad
            self.tempmax = tempmax

            temps = self.tempsurf+self.tempgrad*self.depths/100

        if self.depths.shape == temps.shape:
            self.temps = temps
        else:
            raise("The shape does not match for depths and temps.")

    def get_temp(self,depth):

        dummy_depth = numpy.abs(self.depths-depth)

        index = numpy.where(dummy_depth==dummy_depth.min())[0][0]

        return self.temps[index]+self.tempgrad*(depth-self.depths[index])/100

    def get_unknownthickness(self):

        node_top = numpy.roll(self.depths,1)
        node_bottom = numpy.roll(self.depths,-1)

        thickness = (node_bottom-node_top)/2

        thickness[0] = (self.depths[1]-self.depths[0])/2
        thickness[-1] = (self.depths[-1]-self.depths[-2])/2

        return numpy.sum(thickness[numpy.isnan(self.values)])

    def get_shalevolume(self,spsand=None,spshale=None):

        if spsand is None:
            spsand = numpy.nanmin(self.values)

        if spshale is None:
            spshale = numpy.nanmax(self.values)

        return (self.values-spsand)/(spshale-spsand)

    def get_cut(self,percent,spsand=None,spshale=None):

        if spsand is None:
            spsand = numpy.nanmin(self.values)

        if spshale is None:
            spshale = numpy.nanmax(self.values)

        return (percent/100.)*(spshale-spsand)+spsand

    def get_netthickness(self,percent,**kwargs):

        spcut = self.get_cut(percent,**kwargs)

        node_top = numpy.roll(self.depths,1)
        node_bottom = numpy.roll(self.depths,-1)

        thickness = (node_bottom-node_top)/2

        thickness[0] = (self.depths[1]-self.depths[0])/2
        thickness[-1] = (self.depths[-1]-self.depths[-2])/2

        return numpy.sum(thickness[self.values<spcut])

    def get_netgrossratio(self,percent,**kwargs):

        return self.get_netthickness(percent,**kwargs)/self.grossthickness

    def get_formwaterres(self,method='bateman_and_konen',**kwargs):

        return getattr(self,f"_{method}")(**kwargs)

    def _bateman_and_konen(self,SSP,resmf,resmf_temp,depth):

        temp_depth = self.get_temp(depth)

        resmf_75F = self._restemp_conversion(resmf,resmf_temp,75)

        if resmf_75F>0.1:
        	resmfe_75F = 0.85*resmf_75F
        else:
        	resmfe_75F = (146*resmf_75F-5)/(377*resmf_75F+77)

        K = 60+0.133*temp_depth

        reswe_75F = resmfe_75F/10**(-SSP/K)

        if reswe_75F>0.12:
        	resw_75F = -(0.58-10**(0.69*reswe_75F-0.24))
        else:
        	resw_75F = (77*reswe_75F+5)/(146-377*reswe_75F)

        return self._restemp_conversion(resw_75F,75,temp_depth)

    def _silva_and_bassiouni(self):

    	return Rw

    @property
    def grossthickness(self):

        return self.depths.max()-self.depths.min()

    @staticmethod
    def _restemp_conversion(res1,T1,T2):

    	return res1*(T1+6.77)/(T2+6.77)

class laterolog():

    def __init__(self,values,depths=None):

        self.values = values
        self.depths = depths

    def get_porosity(self):

        pass

class induction():

    def __init__(self,values,depths=None):

        self.values = values
        self.depths = depths

    def get_porosity(self):

        pass

class quantum():

    def __init__(self,values,depths=None):

        self.values = values
        self.depths = depths

    def get_porosity(self):

        pass

# LITHOLOGY MODELING

class denneu():

    def __init__(self,rhof=1.0,phiNf=1.0,NTool="CNL"):

        self.rhof = rhof
        self.phiNf = phiNf

        self.NTool = NTool

        self.Dens = {}
        self.Neus = {}

        self.lithos()

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

class sonden():

    def __init__(self):

        pass

class sonneu():

    def __init__(self,DT_FLUID=189,PHI_NF=1):

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

class mnplot():

    def __init__(self,DTf=189,rhof=1.0,phiNf=1.0,NTool="SNP"):

        self.DTf = DTf
        self.rhof = rhof
        self.phiNf = phiNf

        self.NTool = NTool

        self.Ms = {}
        self.Ns = {}

        self.lithos()

    def MValue(self,DT,rhob):

        return (self.DTf-DT)/(rhob-self.rhof)*0.01

    def NValue(self,PhiN,rhob):

        return (self.phiNf-PhiN)/(rhob-self.rhof)

    def lithos(self):

        phima = f"phima_{self.NTool}"

        self.Ms["SS1"] = self.MValue(self.SS["type1"]["DTma"],self.SS["type1"]["rhoma"])
        self.Ns["SS1"] = self.NValue(self.SS["type1"][phima],self.SS["type1"]["rhoma"])

        self.Ms["SS2"] = self.MValue(self.SS["type2"]["DTma"],self.SS["type2"]["rhoma"])
        self.Ns["SS2"] = self.NValue(self.SS["type2"][phima],self.SS["type2"]["rhoma"])

        self.Ms["LS1"] = self.MValue(self.LS["type1"]["DTma"],self.LS["type1"]["rhoma"])
        self.Ns["LS1"] = self.NValue(self.LS["type1"][phima],self.LS["type1"]["rhoma"])

        self.Ms["DOL1"] = self.MValue(self.DOL["type1"]["DTma"],self.DOL["type1"]["rhoma"])
        self.Ns["DOL1"] = self.NValue(self.DOL["type1"][phima],self.DOL["type1"]["rhoma"])

        self.Ms["DOL2"] = self.MValue(self.DOL["type2"]["DTma"],self.DOL["type2"]["rhoma"])
        self.Ns["DOL2"] = self.NValue(self.DOL["type2"][phima],self.DOL["type2"]["rhoma"])

        self.Ms["DOL3"] = self.MValue(self.DOL["type3"]["DTma"],self.DOL["type3"]["rhoma"])
        self.Ns["DOL3"] = self.NValue(self.DOL["type3"][phima],self.DOL["type3"]["rhoma"])

        self.Ms["ANH1"] = self.MValue(self.ANH["type1"]["DTma"],self.ANH["type1"]["rhoma"])
        self.Ns["ANH1"] = self.NValue(self.ANH["type1"][phima],self.ANH["type1"]["rhoma"])

        self.Ms["SLT1"] = self.MValue(self.SLT["type1"]["DTma"],self.SLT["type1"]["rhoma"])
        self.Ns["SLT1"] = self.NValue(self.SLT["type1"][phima],self.SLT["type1"]["rhoma"])

    def lithonodes(self,axis):

        NSS  = [self.Ns["SS1"],self.Ns["SS2"]]
        MSS  = [self.Ms["SS1"],self.Ms["SS2"]]
        NLS  = [self.Ns["LS1"]]
        MLS  = [self.Ms["LS1"]]
        NDOL = [self.Ns["DOL1"],self.Ns["DOL2"],self.Ns["DOL3"]]
        MDOL = [self.Ms["DOL1"],self.Ms["DOL2"],self.Ms["DOL3"]]
        NANH = [self.Ns["ANH1"]]
        MANH = [self.Ms["ANH1"]]
        NSLT = [self.Ns["SLT1"]]
        MSLT = [self.Ms["SLT1"]]

        axis.plot(NSS,MSS,label=self.SS["lithology"],
            linestyle="None",
            marker=self.SS["marker"],
            markerfacecolor=self.SS["markercolor"],
            markeredgecolor=self.SS["markercolor"])

        axis.plot(NLS,MLS,label=self.LS["lithology"],
            linestyle="None",
            marker=self.LS["marker"],
            markerfacecolor=self.LS["markercolor"],
            markeredgecolor=self.LS["markercolor"])

        axis.plot(NDOL,MDOL,label=self.DOL["lithology"],
            linestyle="None",
            marker=self.DOL["marker"],
            markerfacecolor=self.DOL["markercolor"],
            markeredgecolor=self.DOL["markercolor"])

        axis.plot(NANH,MANH,label=self.ANH["lithology"],
            linestyle="None",
            marker=self.ANH["marker"],
            markerfacecolor=self.ANH["markercolor"],
            markeredgecolor=self.ANH["markercolor"])

        axis.plot(NSLT,MSLT,label=self.SLT["lithology"],
            linestyle="None",
            marker=self.SLT["marker"],
            markerfacecolor=self.SLT["markercolor"],
            markeredgecolor=self.SLT["markercolor"])

        axis.set_xlabel("N-values")
        axis.set_ylabel("M-values")

        axis.legend(loc="upper center",ncol=3,bbox_to_anchor=(0.5,1.15))

        axis.set_xlim((0.3,1))
        axis.set_ylim((0.5,1.2))

        xmajor_ticks = numpy.arange(0.3,1.01,0.1)
        xminor_ticks = numpy.arange(0.3,1.01,0.02)

        ymajor_ticks = numpy.arange(0.5,1.21,0.1)
        yminor_ticks = numpy.arange(0.5,1.21,0.02)

        axis.set_xticks(xmajor_ticks,minor=False)
        axis.set_xticks(xminor_ticks,minor=True)

        axis.set_yticks(ymajor_ticks,minor=False)
        axis.set_yticks(yminor_ticks,minor=True)

        axis.grid(which='both')

        axis.grid(which='minor',alpha=0.2)
        axis.grid(which='major',alpha=0.5)

        return axis

    def ternary(self,axis,lith1="SS1",lith2="LS1",lith3="DOL1",num=10):

        p1 = [self.Ns[lith1],self.Ms[lith1]]
        p2 = [self.Ns[lith2],self.Ms[lith2]]
        p3 = [self.Ns[lith3],self.Ms[lith3]]

        nodes = [p1,p2,p3]

        xmin = min((p1[0],p2[0],p3[0]))
        xmax = max((p1[0],p2[0],p3[0]))

        ymin = min((p1[1],p2[1],p3[1]))
        ymax = max((p1[1],p2[1],p3[1]))

        xmin = 0.3+int((xmin-0.3)/0.02)*0.02
        xmax = 1.0-int((1.0-xmax)/0.02)*0.02

        ymin = 0.5+int((ymin-0.5)/0.02)*0.02
        ymax = 1.2-int((1.2-ymax)/0.02)*0.02

        axis.plot([p1[0],p2[0]],[p1[1],p2[1]],'k',linewidth=0.5)
        axis.plot([p2[0],p3[0]],[p2[1],p3[1]],'k',linewidth=0.5)
        axis.plot([p3[0],p1[0]],[p3[1],p1[1]],'k',linewidth=0.5)

        axis.set_xlim([xmin,xmax])
        axis.set_ylim([ymin,ymax])

        xmajor_ticks = numpy.arange(xmin,xmax+1e-5,0.02)

        if xmajor_ticks.size<10:
            axis.set_xticks(xmajor_ticks,minor=False)

        ymajor_ticks = numpy.arange(ymin,ymax+1e-5,0.02)

        if ymajor_ticks.size<10:
            axis.set_yticks(ymajor_ticks,minor=False)

        axis.grid(visible=True)

        index = numpy.arange(1,num)

        xs1 = p1[0]+index*(p2[0]-p1[0])/num
        xs2 = p2[0]+index*(p3[0]-p2[0])/num
        xs3 = p3[0]+index*(p1[0]-p3[0])/num

        ys1 = p1[1]+index*(p2[1]-p1[1])/num
        ys2 = p2[1]+index*(p3[1]-p2[1])/num
        ys3 = p3[1]+index*(p1[1]-p3[1])/num

        axis.plot([p1[0],p2[0]],[p1[1],p2[1]],'k',linewidth=0.5)
        axis.plot([p2[0],p3[0]],[p2[1],p3[1]],'k',linewidth=0.5)
        axis.plot([p3[0],p1[0]],[p3[1],p1[1]],'k',linewidth=0.5)

        for i in index:
            axis.plot([xs1[i-1],xs2[num-1-i]],[ys1[i-1],ys2[num-1-i]],'k',linewidth=0.5)
            axis.plot([xs2[i-1],xs3[num-1-i]],[ys2[i-1],ys3[num-1-i]],'k',linewidth=0.5)
            axis.plot([xs3[i-1],xs1[num-1-i]],[ys3[i-1],ys1[num-1-i]],'k',linewidth=0.5)

        return axis,nodes

    def lithoratio(self,nodes):
        
        pass

class midplot():

    def __init__(self):

        self.fig_midp,self.axis_midp = pyplot.subplots()

class rhoumaa():

    def __init__(self):

        pass

# SATURATION MODELING

class pickett():

    def __init__(self,offsets,slope=None,intercept=None,m=2,a=1,Rw=0.01,n=2):
        """offsets is Nx2 matrix, first column is (x-axis) resistivity and the second is (y-axis) porosity."""

        self.offsets = offsets

        self.archie_m = m
        self.archie_a = a
        self.archie_Rw = Rw
        self.archie_n = n

        if slope is None:
            slope = -self.archie_m

        self.slope = slope

        if intercept is None:
            intercept = numpy.log10(self.archie_a*self.archie_Rw)

        self.intercept = intercept

    def set_axis(self,axis=None):

        if axis is None:
            figure,axis = pyplot.subplots(nrows=1,ncols=1)

        self.axis = axis

        self.axis.scatter(*self.offsets.T,s=2,c="k")

        self.axis.set_xscale('log')
        self.axis.set_yscale('log')

        xlim = numpy.array(self.axis.get_xlim())
        ylim = numpy.array(self.axis.get_ylim())

        self.xlim = numpy.floor(numpy.log10(xlim))+numpy.array([0,1])
        self.ylim = numpy.floor(numpy.log10(ylim))+numpy.array([0,1])

        self.axis.set_xlabel("x-axis")
        self.axis.set_ylabel("y-axis")

        self.axis.set_xlim(10**self.xlim)
        self.axis.set_ylim(10**self.ylim)

        fstring = 'x={:1.3f} y={:1.3f} m={:1.3f} b={:1.3f}'

        self.axis.format_coord = lambda x,y: fstring.format(x,y,-self.slope,self.intercept)

        self.lines = []

        self.canvas = self.axis.figure.canvas

    def set_lines(self,*args):
        """arguments must be water saturation percentage in a decreasing order!"""

        saturations = [100]

        [saturations.append(arg) for arg in args]

        base = self.slope*self.xlim+self.intercept

        for line in self.lines:

            line.remove()

        self.lines = []

        linewidth = 1.0

        alpha = 1.0

        X = 10**self.xlim

        for saturation in saturations:

            Y = 10**(base-self.archie_n*numpy.log10(saturation/100))

            line, = self.axis.plot(X,Y,linewidth=linewidth,color="blue",alpha=alpha)

            linewidth -= 0.1

            alpha -= 0.1

            self.lines.append(line)

        self.canvas.draw()

    def set_mouse(self):

        self.pressed = False
        self.start = False

        self.canvas.mpl_connect('button_press_event',self._mouse_press)
        self.canvas.mpl_connect('motion_notify_event',self._mouse_move)
        self.canvas.mpl_connect('button_release_event',self._mouse_release)

    def _mouse_press(self,event):

        if self.axis.get_navigate_mode()!= None: return
        if not event.inaxes: return
        if event.inaxes != self.axis: return

        if self.start: return

        if event.button is not MouseButton.LEFT: return

        self.pressed = True

    def _mouse_move(self,event):

        if self.axis.get_navigate_mode()!=None: return
        if not event.inaxes: return
        if event.inaxes!=self.axis: return

        if not self.pressed: return

        self.start = True

        x = numpy.log10(event.xdata)
        y = numpy.log10(event.ydata)

        self.intercept = y-self.slope*x

        self.set_lines()

    def _mouse_release(self,event):

        if self.axis.get_navigate_mode()!=None: return
        if not event.inaxes: return
        if event.inaxes!=self.axis: return

        if self.pressed:

            self.pressed = False
            self.start = False

            self.set_lines(50,20,10)

            return

    def show(self):

        pyplot.show()

    def saturation(self):

        res,por = self.offsets.T

        resporm = res*numpy.power(por,-self.slope)

        saturation = numpy.power(10**self.intercept/resporm,1/self.archie_n)

        saturation[saturation>1] = 1

        return saturation

class PickettCrossPlot(): #Will BE DEPRECIATED

    def __init__(
        self,
        resLine,
        phiLine,
        returnSwFlag=False,
        showDiffSwFlag=True,
        m=2,
        n=2,
        a=0.62,
        Rw=0.1,
        xmin=None,
        xmax=None,
        ymin=None,
        ymax=None,
        GRconds=None,
        ):

        if returnSwFlag:

            xvalsR = self.frames[resLine[0]].columns(resLine[1])
            xvalsP = self.frames[phiLine[0]].columns(phiLine[1])

            Sw_calculated = ((a*Rw)/(xvalsR*xvalsP**m))**(1/n)

            Sw_calculated[Sw_calculated>1] = 1

            return Sw_calculated

        else:

            self.fig_pcp,self.axis_pcp = pyplot.subplots()

            xaxis_min = 1
            xaxis_max = 100

            yaxis_min = 0.1
            yaxis_max = 1

            for depth in self.depths:

                xaxis = self.get_interval(*depth[1:],idframes=resLine[0],curveID=resLine[1])[0]
                yaxis = self.get_interval(*depth[1:],idframes=phiLine[0],curveID=phiLine[1])[0]

                xaxis_min = min((xaxis_min,xaxis.min()))
                xaxis_max = max((xaxis_max,xaxis.max()))

                yaxis_min = min((yaxis_min,yaxis.min()))
                yaxis_max = max((yaxis_max,yaxis.max()))

                if GRconds is not None:
                    self.axis_pcp.scatter(xaxis[GRconds],yaxis[GRconds],s=1,label="{} clean".format(depth[0]))
                    self.axis_pcp.scatter(xaxis[~GRconds],yaxis[~GRconds],s=1,label="{} shaly".format(depth[0]))
                else:
                    self.axis_pcp.scatter(xaxis,yaxis,s=1,label=depth[0])

            self.axis_pcp.legend(scatterpoints=10)

            indexR = self.frames[resLine[0]].headers.index(resLine[1])
            indexP = self.frames[phiLine[0]].headers.index(phiLine[1])

            mnemR = self.frames[resLine[0]].headers[indexR]
            unitR = self.frames[resLine[0]].units[indexR]

            mnemP = self.frames[phiLine[0]].headers[indexP]
            unitP = self.frames[phiLine[0]].units[indexP]

            xaxis_min = xmin if xmin is not None else xaxis_min
            xaxis_max = xmax if xmax is not None else xaxis_max

            yaxis_min = ymin if ymin is not None else yaxis_min
            yaxis_max = ymax if ymax is not None else yaxis_max

            resexpmin = numpy.floor(numpy.log10(xaxis_min))
            resexpmax = numpy.ceil(numpy.log10(xaxis_max))

            if showDiffSwFlag:

                resSw = numpy.logspace(resexpmin,resexpmax,100)

                Sw75,Sw50,Sw25 = 0.75,0.50,0.25

                philine_atSw100 = (a*Rw/resSw)**(1/m)

                philine_atSw075 = philine_atSw100*Sw75**(-n/m)
                philine_atSw050 = philine_atSw100*Sw50**(-n/m)
                philine_atSw025 = philine_atSw100*Sw25**(-n/m)

                self.axis_pcp.plot(resSw,philine_atSw100,c="black",linewidth=1)#,label="100% Sw")
                self.axis_pcp.plot(resSw,philine_atSw075,c="blue",linewidth=1)#,label="75% Sw")
                self.axis_pcp.plot(resSw,philine_atSw050,c="blue",linewidth=1)#,label="50% Sw")
                self.axis_pcp.plot(resSw,philine_atSw025,c="blue",linewidth=1)#,label="25% Sw")

            phiexpmin = numpy.floor(numpy.log10(yaxis_min))
            phiexpmax = numpy.ceil(numpy.log10(yaxis_max))

            xticks = 10**numpy.arange(resexpmin,resexpmax+1/2)
            yticks = 10**numpy.arange(phiexpmin,phiexpmax+1/2)

            self.axis_pcp.set_xscale('log')
            self.axis_pcp.set_yscale('log')

            self.axis_pcp.set_xlim([xticks.min(),xticks.max()])
            self.axis_pcp.set_xticks(xticks)

            self.axis_pcp.set_ylim([yticks.min(),yticks.max()])
            self.axis_pcp.set_yticks(yticks)

            self.axis_pcp.xaxis.set_major_formatter(LogFormatter())
            self.axis_pcp.yaxis.set_major_formatter(LogFormatter())

            for tic in self.axis_pcp.xaxis.get_minor_ticks():
                tic.label1.set_visible(False)
                tic.tick1line.set_visible(False)

            for tic in self.axis_pcp.yaxis.get_minor_ticks():
                tic.label1.set_visible(False)
                tic.tick1line.set_visible(False)

            self.axis_pcp.set_xlabel("{} {}".format(mnemR,unitR))
            self.axis_pcp.set_ylabel("{} {}".format(mnemP,unitP))

            self.axis_pcp.grid(True,which="both",axis='both')

class hingle():

    def __init__(self):

        pass

    def HingleCrossPlot(self):

        self.fig_hcp,self.axis_hcp = pyplot.subplots()