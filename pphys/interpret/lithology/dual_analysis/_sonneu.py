import numpy

from borepy.utils._wrappers import trim

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