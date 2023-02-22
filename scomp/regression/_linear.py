import numpy

from scipy import stats

class LinearSimple():
    """Simple Linear Regression Model"""

    def __init__(self,yvals,xvals):

        self.yvals = yvals
        self.xvals = xvals

    def train(self):

        self.xmean = self.xvals.mean()
        self.ymean = self.yvals.mean()

        xdiff = self.xvals-self.xmean
        ydiff = self.yvals-self.ymean

        self.Sxx = numpy.sum(xdiff*xdiff)
        self.Syy = numpy.sum(ydiff*ydiff)
        self.Sxy = numpy.sum(xdiff*ydiff)

        # b1 is the estimate of the beta1 (beta1 is true model slope)
        self.b1 = self.Sxy/self.Sxx

        # b0 is the estimate of the beta0 (beta0 is true model intercept)
        self.b0 = self.ymean-self.b1*self.xmean

        # sum of squares of the errors
        self.SSE = self.Syy-self.b1*self.Sxy

        # number of trained data
        self.size = self.xvals.size

        # s2 is an unbiased estimate of sigma2 (sigma2 is error variance in the true model)
        self.s2 = self.SSE/(self.size-2)

        # coefficient of determination
        self.R2 = 1-self.SSE/self.Syy

    def beta0confint(self,alpha=0.05):
        """It will report 100*(1-alpha)% confidence interval for the beta0, true model intercept."""

        talpha = -stats.t.ppf(alpha/2,df=self.size-2)

        upper = self.s2*numpy.sum(self.xvals**2)
        lower = self.size*self.Sxx

        temp = talpha*(upper/lower)**(1/2)

        return self.b0-temp,self.b0+temp

    def beta1confint(self,alpha=0.05):
        """It will report 100*(1-alpha)% confidence interval for the beta1, true model slope."""

        talpha = -stats.t.ppf(alpha/2,df=self.size-2)

        temp = talpha*(self.s2/self.Sxx)**(1/2)

        return self.b1-temp,self.b1+temp

    def beta0test(self,beta00):
        """It returns the alpha value for tested beta00."""

        upper = self.s2*numpy.sum(self.xvals**2)
        lower = self.size*self.Sxx

        tscore = abs(self.b0-beta00)/((upper/lower)**(1/2))
        # print(f"{tscore = }")

        return stats.t.cdf(-tscore,self.size-2)

    def beta1test(self,beta10):
        """It returns the alpha value for tested beta10."""

        tscore = abs(self.b1-beta10)/(self.s2/self.Sxx)**(1/2)
        # print(f"{tscore = }")

        return stats.t.cdf(-tscore,self.size-2)

    def estimate(self,points):

        return self.b0+self.b1*numpy.array(points)

    def meanconfint(self,points,alpha=0.05):
        """It will report 100*(1-alpha)% confidence interval for the mean value of true model."""

        y0 = self.estimate(points)

        talpha = -stats.t.ppf(alpha/2,df=self.size-2)

        temp = 1/self.size+(points-self.xmean)**2/self.Sxx

        temp = talpha*(self.s2*temp)**(1/2)

        return y0-temp,y0+temp

    def predict(self,points,alpha=0.05):

        y0 = self.estimate(points)

        talpha = -stats.t.ppf(alpha/2,df=self.size-2)

        temp = 1+1/self.size+(points-self.xmean)**2/self.Sxx

        temp = talpha*(self.s2*temp)**(1/2)

        return y0-temp,y0+temp

class LinearMultiple():

    def __init__(self,yvals,*args):

        self.yvals = numpy.array(yvals)
        self.xvals = [numpy.array(xk) for xk in args]

    def train(self):

        self.size = self.yvals.size

        Nmat = len(self.xvals)+1

        Amat = numpy.zeros((Nmat,Nmat))
        Zmat = numpy.zeros((Nmat))

        for i in range(Nmat):

            xi = 1 if i==0 else self.xvals[i-1]

            for j in range(Nmat):

                xj = 1 if j==0 else self.xvals[j-1]

                Amat[i,j] = numpy.sum(xi*xj)

            Zmat[i] = numpy.sum(xi*self.yvals)

        Amat[0,0] = self.size

        self.bs = numpy.linalg.solve(Amat,Zmat)

        for index,b in enumerate(self.bs):

            setattr(self,f"b{index}",b)


class Stepwise():

    def __init__(self):

        pass