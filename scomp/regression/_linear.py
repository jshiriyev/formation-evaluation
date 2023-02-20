import numpy

from scipy import stats

class Linear():

    def __init__(self,xvals,yvals):

        self.xvals = xvals
        self.yvals = yvals

    def train(self):

        xavg = self.xvals.mean()
        yavg = self.yvals.mean()

        self.Sxx = numpy.sum((self.xvals-xavg)**2)
        self.Syy = numpy.sum((self.yvals-yavg)**2)
        self.Sxy = numpy.sum((self.xvals-xavg)*(self.yvals-yavg))

        self.b1 = self.Sxy/self.Sxx
        self.b0 = yavg-self.b1*xavg

        self.SSE = self.Syy-self.b1*self.Sxy

        self.N = self.xvals.size

        self.s2 = self.SSE/(self.N-2)

        self.s = numpy.sqrt(self.s2)

        self.R2 = 1-self.SSE/self.Syy

    def b0ci(self,alpha):

        talpha2 = stats.t.ppf(alpha/2,df=self.N-2)

        temp = numpy.sum(self.xvals**2)/(self.N*self.Sxx)

        lower = self.b0+talpha2*self.s*temp**(1/2)
        upper = self.b0-talpha2*self.s*temp**(1/2)

        return lower,upper

    def b1ci(self,alpha):

        talpha2 = stats.t.ppf(alpha/2,df=self.N-2)

        lower = self.b1+talpha2*self.s/self.Sxx**(1/2)
        upper = self.b1-talpha2*self.s/self.Sxx**(1/2)

        return lower,upper

    def b0test(self,beta):

        temp = numpy.sum(self.xvals**2)/(self.N*self.Sxx)

        tscore = (self.b0-beta)/(self.s*temp**(1/2))

        print(tscore)

        alpha = stats.t.cdf(tscore,self.N-2)

        return alpha

    def b1test(self,beta):

        tscore = (self.b1-beta)/self.s*self.Sxx**(1/2)

        print(tscore)

        alpha = stats.t.cdf(tscore,self.N-2)

        return alpha

    def estimate(self,points):

        return self.b0+self.b1*numpy.array(points)

