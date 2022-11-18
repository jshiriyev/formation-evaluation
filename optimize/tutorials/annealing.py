import matplotlib.pyplot as plt

import numpy as np

if __name__ == "__main__":
    import setup

from optimize.global_search import annealing

def testfunc(m):

    if type(m) is not np.ndarray:
        m = np.array([m])

    lhs = np.sign(np.sinc(m))
    rhs = np.power(np.abs(np.sinc(m)),1./4)
    
    capi = np.prod(lhs*rhs,1)
    cost = np.power(1.-capi,2.)
    
    return cost

if __name__ == "__main__":

    m = np.linspace(-10,10,1000)

    E = testfunc(np.array([m]).T)

    plt.plot(m,E)
    plt.show()

    # nog = 100   #50
    # nom = 25    #3
    # nop = 5     #2

    # m_min = np.ones([1,nop])*-10    #0,0
    # m_max = np.ones([1,nop])*10     #10,10

    # model = annealing(m_min,m_max,nog,nom,nop)

    # #T = model.temperature('straight') #straight
    # T = model.temperature('geometric')
    # #T = model.temperature('reciprocal')
    # #T = model.temperature('logarithmic')

    # model.iterating(testfunc)

    # plt.figure(num=1)

    # X = np.array(range(1,nog+1))

    # plt.plot(X,T1)
    # plt.plot(X,T2)
    # plt.plot(X,T3)
    # plt.plot(X,T4)

    # plt.xlim([0.,nog])
    # plt.ylim([0.,1.])

    # plt.show()
