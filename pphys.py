import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

from matplotlib.patches import Rectangle

import numpy

class colors():

    def __init__(self,**kwargs):

        self.SH         = ("Shale","gray",None)
        self.clean      = ("Clean Formation","tan",None)
        self.SS         = ("Sandstone","gold","..")
        self.LS         = ("Limestone","navajowhite","-")
        self.DOL        = ("Dolomite","darkkhaki","/")
        self.fluid      = ("Pore Volume","white","o")

        self.liquid     = ("Liquid","blue","O")
        self.water      = ("Water","aqua","OO")
        self.waterCLAY  = ("Water Clay Bound","lightskyblue","X")
        self.waterCAP   = ("Water Capillary Bound","lightsteelblue","X")
        self.waterIRRE  = ("Water Irreducible","lightblue","X")
        self.waterM     = ("Water Movable","steelblue",None)
        self.fluidM     = ("Fluid Movable","seagreen",None)

        self.HC         = ("Hydrocarbon","green",None)
        self.gas        = ("Gas","red","oo")
        self.gasR       = ("Gas Residual","red",None)
        self.gasM       = ("Gas Movable","red",None)
        self.oil        = ("Oil","limegreen",None)
        self.oilR       = ("Oil Residual","limegreen",None)
        self.oilM       = ("Oil Movable","limegreen",None)
        
        self.set_colors(**kwargs)

    def set_colors(self,**kwargs):

        for key,value in kwargs.items():

            try:
                mcolors.to_rgba(value)
            except ValueError:
                raise ValueError(f"Invalid RGBA argument: '{value}'")

            getattr(self,key)[1] = value

    def set_hatches(self,**kwargs):

        for key,value in kwargs.items():

            getattr(self,key)[2] = value

    def view(self,axis,nrows=(6,7,7),ncols=3,fontsize=10,sizes=(8,5),dpi=100):

        X,Y = [dpi*size for size in sizes]

        w = X/ncols
        h = Y/(max(nrows)+1)

        names = self.names

        colors = self.colors

        hatches = self.hatches

        k = 0
            
        for idcol in range(ncols):

            for idrow in range(nrows[idcol]):

                y = Y-(idrow*h)-h

                xmin = w*(idcol+0.05)
                xmax = w*(idcol+0.25)

                ymin = y-h*0.3
                ymax = y+h*0.3

                xtext = w*(idcol+0.3)

                axis.text(xtext,y,names[k],fontsize=(fontsize),
                        horizontalalignment='left',
                        verticalalignment='center')

                axis.add_patch(
                    Rectangle((xmin,ymin),xmax-xmin,ymax-ymin,
                    fill=True,hatch=hatches[k],facecolor=colors[k]))

                k += 1

        axis.set_xlim(0,X)
        axis.set_ylim(0,Y)

        axis.set_axis_off()

        return axis

    @property
    def items(self):
        return list(self.__dict__.keys())
    
    @property
    def names(self):
        return [value[0] for key,value in self.__dict__.items()]

    @property
    def colors(self):
        return [value[1] for key,value in self.__dict__.items()]

    @property
    def hatches(self):
        return [value[2] for key,value in self.__dict__.items()]

def GRcut(self,GRline,depth=("None",None,None),perc_cut=40):

    xvals = self.get_interval(*depth[1:],idframes=GRline[0],curveID=GRline[1])[0]

    GRmin = numpy.nanmin(xvals)
    GRmax = numpy.nanmax(xvals)

    GRcut = (GRmin+(GRmax-GRmin)*perc_cut/100)

    return GRcut

def ShaleVolumeGR(self,GRline,GRmin=None,GRmax=None,model=None):

    xvals = self.frames[GRline[0]][GRline[1]]

    if GRmin is None:
        GRmin = numpy.nanmin(xvals)

    if GRmax is None:
        GRmax = numpy.nanmax(xvals)

    Ish = (xvals-GRmin)/(GRmax-GRmin)

    if model is None or model=="linear":
        Vsh = Ish

    return Vsh

def ShaleVolumeSP(self,SPline,SPsand,SPshale):

    xvals = self.frames[SPline[0]][SPline[1]]

    Vsh = (xvals-SPsand)/(SPshale-SPsand)

    return Vsh

def GammaSpecCrossPlot(self):

    self.fig_gscp,self.axis_gscp = pyplot.subplots()

def DenNeuCrossPlot(self):

    self.fig_dncp,self.axis_dncp = pyplot.subplots()

def SonDenCrossPlot(self):

    self.fig_sdcp,self.axis_sdcp = pyplot.subplots()

def SonNeuCrossPlot(self,
    porLine,
    sonLine,
    a_SND=+0.00,
    a_LMS=+0.00,
    a_DOL=-0.06,
    b_SND=+0.90,
    b_LMS=+0.80,
    b_DOL=+0.84,
    p_SND=+0.02,
    p_LMS=+0.00,
    p_DOL=-0.01,
    DT_FLUID=189,
    DT_SND=55.6,
    DT_LMS=47.5,
    DT_DOL=43.5,
    xmin=None,
    ymin=None,
    xmax=None,
    ymax=None,
    rotate=0):

    self.fig_sncp,self.axis_sncp = pyplot.subplots()

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

def DenPheCrossPlot(self):

    # density photoelectric cross section cross plot

    self.fig_dpcp,self.axis_dpcp = pyplot.subplots()

class MNplot():

    def __init__(self):

        self.SS1    = {"name": "Sandstone, Porosity>10%",
            "DTma": 55.5,"rhoma": 2.65,"phima_SNP": -0.035,"phima_CLN": -0.05}
        self.SS2    = {"name": "Sandstone, Porosity<10%",
            "DTma": 51.2,"rhoma": 2.65,"phima_SNP": -0.035,"phima_CLN": -0.005}
        self.LS     = {"name": "Limestone",
            "DTma": 47.5,"rhoma": 2.71,"phima_SNP": 0,"phima_CLN": 0}
        self.DOL1   = {"name": "Dolomite, 5.5%<Porosity<30%",
            "DTma": 43.5,"rhoma": 2.87,"phima_SNP": 0.035,"phima_CLN": 0.085}
        self.DOL2   = {"name": "Dolomite, 1.5%<Porosity<5.5% and Porosity>30%",
            "DTma": 43.5,"rhoma": 2.87,"phima_SNP": 0.02,"phima_CLN": 0.065}
        self.DOL3   = {"name": "Dolomite, 5.5%<Porosity<30%",
            "DTma": 43.5,"rhoma": 2.87,"phima_SNP": 0.005,"phima_CLN": 0.04}
        self.ANHY   = {"name": "Anhydrite",
            "DTma": 50.0,"rhoma": 2.98,"phima_SNP": -0.005,"phima_CLN": -0.002}
        self.SALT   = {"name": "Salt",
            "DTma": 67.0,"rhoma": 2.03,"phima_SNP": 0.04,"phima_CLN": -0.01}

    def Mvalue(self,DT,rho_b,DT_f=189,rho_f=1.0):
        return (DT_f-DT)/(rho_b-rho_f)*0.01

    def Nvalue(self,Phi_N,rho_b,Phi_Nf=1.0,rho_f=1.0):
        return (Phi_Nf-Phi_N)/(rho_b-rho_f)

    def ternary(self,axis,number=10):

        M1 = self.Mvalue(self.SS1["DTma"],self.SS1["rhoma"])
        M2 = self.Mvalue(self.LS["DTma"],self.LS["rhoma"])
        M3 = self.Mvalue(self.DOL1["DTma"],self.DOL1["rhoma"])

        N1 = self.Nvalue(self.SS1["phima_SNP"],self.SS1["rhoma"])
        N2 = self.Nvalue(self.LS["phima_SNP"],self.LS["rhoma"])
        N3 = self.Nvalue(self.DOL1["phima_SNP"],self.DOL1["rhoma"])

        p1 = (M1,N1)
        p2 = (M2,N2)
        p3 = (M3,N3)

        index = numpy.arange(1,number)

        xs1 = p1[0]+index*(p2[0]-p1[0])/number
        xs2 = p2[0]+index*(p3[0]-p2[0])/number
        xs3 = p3[0]+index*(p1[0]-p3[0])/number

        ys1 = p1[1]+index*(p2[1]-p1[1])/number
        ys2 = p2[1]+index*(p3[1]-p2[1])/number
        ys3 = p3[1]+index*(p1[1]-p3[1])/number

        axis.plot([p1[0],p2[0]],[p1[1],p2[1]],'k',linewidth=0.5)
        axis.plot([p2[0],p3[0]],[p2[1],p3[1]],'k',linewidth=0.5)
        axis.plot([p3[0],p1[0]],[p3[1],p1[1]],'k',linewidth=0.5)

        for i in index:
            axis.plot([xs1[i-1],xs2[number-1-i]],[ys1[i-1],ys2[number-1-i]],'k',linewidth=0.5)
            axis.plot([xs2[i-1],xs3[number-1-i]],[ys2[i-1],ys3[number-1-i]],'k',linewidth=0.5)
            axis.plot([xs3[i-1],xs1[number-1-i]],[ys3[i-1],ys1[number-1-i]],'k',linewidth=0.5)

        return axis

def MIDplot(self):

    self.fig_midp,self.axis_midp = pyplot.subplots()

def RhomaaUmaaPlot(self):

    self.fig_rhoU,self.axis_rhoU = pyplot.subplots()

def PickettCrossPlot(
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

def HingleCrossPlot(self):

    self.fig_hcp,self.axis_hcp = pyplot.subplots()
