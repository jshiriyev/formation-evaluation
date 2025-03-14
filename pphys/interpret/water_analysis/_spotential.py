class spotential():

    def __init__(self,SP=None,TEMP=None):
        """Initialization of output signals."""

        self.SP = SP

        self.TEMP = TEMP

    def config(self,**kwargs):
        """Setting tool configuration."""

        pass

    def get_temp(self,depthpoint):
        """Returns the temperature at the given depth based on interpolation of TEMP curve."""

        indices = numpy.argpartition(numpy.abs(self.depth-depthpoint),2)[:2]

        Dtop,Dbottom = self.depth[indices]
        Ttop,Tbottom = self.TEMP[indices]

        temp = Ttop+(Tbottom-Ttop)*(depthpoint-Dtop)/(Dbottom-Dtop)

        return temp

    def shalevolume(self,spsand=None,spshale=None):

        if spsand is None:
            spsand = self.SP.min()

        if spshale is None:
            spshale = self.SP.max()

        Vsh = (self.SP.vals-spsand)/(spshale-spsand)

        info = 'Shale volume calculated from spontaneous potential.'

        return LasCurve(
            depth = self.SP.depth,
            vals = Vsh,
            head = 'VSH',
            unit = '-',
            info = info)

    def cut(self,percent,spsand=None,spshale=None):

        if spsand is None:
            spsand = self.SP.min()

        if spshale is None:
            spshale = self.SP.max()

        return (percent/100.)*(spshale-spsand)+spsand

    def netthickness(self,percent,**kwargs):

        spcut = self.cut(percent,**kwargs)

        node_top = numpy.roll(self.SP.depth,1)
        node_bottom = numpy.roll(self.SP.depth,-1)

        thickness = (node_bottom-node_top)/2

        thickness[0] = (self.SP.depth[1].vals[0]-self.SP.depth[0].vals[0])/2
        thickness[-1] = (self.SP.depth[-1].vals[0]-self.SP.depth[-2].vals[0])/2

        return numpy.sum(thickness[self.SP.vals<spcut])

    def nettogrossratio(self,percent,**kwargs):

        return self.netthickness(percent,**kwargs)/self.SP.height['total']

    def formwaterres(self,method='bateman_and_konen',**kwargs):

        return getattr(self,f"{method}")(**kwargs)

    def bateman_and_konen(self,SSP,resmf,resmf_temp,depthpoint):

        resmf_75F = self.restemp_conversion(resmf,resmf_temp,75)

        if resmf_75F>0.1:
            resmfe_75F = 0.85*resmf_75F
        else:
            resmfe_75F = (146*resmf_75F-5)/(377*resmf_75F+77)

        K = 60+0.133*self.get_temp(depthpoint)

        reswe_75F = resmfe_75F/10**(-SSP/K)

        if reswe_75F>0.12:
            resw_75F = -(0.58-10**(0.69*reswe_75F-0.24))
        else:
            resw_75F = (77*reswe_75F+5)/(146-377*reswe_75F)

        return self.restemp_conversion(resw_75F,75,self.get_temp(depthpoint))

    def silva_and_bassiouni(self):

        return Rw

    @staticmethod
    def restemp_conversion(res1,T1,T2):

        return res1*(T1+6.77)/(T2+6.77)

    @property
    def depth(self):

        return self.SP.depth