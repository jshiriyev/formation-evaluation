class mnplot():

    def __init__(self,DTf=189,rhof=1.0,phiNf=1.0,NTool="SNP",**kwargs):

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