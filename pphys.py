color_sandstone = "gold"
color_limestone = "navajowhite"
color_dolomite  = "darkkhaki"
color_clean     = "tan"
color_shale     = "gray"
color_waterclay = "lightskyblue"
color_watercapi = "lightsteelblue"
color_waterirre = "lightblue"
color_watermove = "steelblue"
color_water     = "aqua"
color_HC        = "green"
color_oil       = "limegreen"
color_gas       = "lightgreen"
color_fluidmove = "seagreen"

def get_GRcut(self,GRline,depth=("None",None,None),perc_cut=40):

    xvals = self.get_interval(*depth[1:],idframes=GRline[0],curveID=GRline[1])[0]

    GRmin = numpy.nanmin(xvals)
    GRmax = numpy.nanmax(xvals)

    GRcut = (GRmin+(GRmax-GRmin)*perc_cut/100)

    return GRcut

def get_ShaleVolumeGR(self,GRline,GRmin=None,GRmax=None,model=None):

    xvals = self.frames[GRline[0]][GRline[1]]

    if GRmin is None:
        GRmin = numpy.nanmin(xvals)

    if GRmax is None:
        GRmax = numpy.nanmax(xvals)

    Ish = (xvals-GRmin)/(GRmax-GRmin)

    if model is None or model=="linear":
        Vsh = Ish

    return Vsh

def get_ShaleVolumeSP(self,SPline,SPsand,SPshale):

    xvals = self.frames[SPline[0]][SPline[1]]

    Vsh = (xvals-SPsand)/(SPshale-SPsand)

    return Vsh

def set_GammaSpectralCP(self):

    self.fig_gscp,self.axis_gscp = pyplot.subplots()

def set_DenNeuCP(self):

    self.fig_dncp,self.axis_dncp = pyplot.subplots()

def set_SonDenCP(self):

    self.fig_sdcp,self.axis_sdcp = pyplot.subplots()

def set_SonNeuCP(self,
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

def set_DenPheCP(self):

    # density photoelectric cross section cross plot

    self.fig_dpcp,self.axis_dpcp = pyplot.subplots()

def set_MNplot(self):

    self.fig_mncp,self.axis_mncp = pyplot.subplots()

def set_MIDplot(self):

    self.fig_midp,self.axis_midp = pyplot.subplots()

def set_rhomaaUmaa(self):

    self.fig_rhoU,self.axis_rhoU = pyplot.subplots()

def set_PickettCP(
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

def set_HingleCP(self):

    self.fig_hcp,self.axis_hcp = pyplot.subplots()
