import numpy as np
from ipdb import set_trace as debug
import pylab as plt
import seaborn as sns
from seaborn import xkcd_rgb as xkcd



class Line(object):

    def __init__(self, x, y, eps):
        self.x = x
        self.y = y
        self.eps = eps

    def fit(self, i0, i1):
        self.i0 = i0
        self.i1 = i1
        self.m = (self.y[i1] - self.y[i0])/(self.x[i1] - self.x[i0])
        self.b = self.y[i1] - self.m * self.x[i1] 

    def eval(self, x):
        return self.m * x + self.b

    @property
    def valid(self):
        for k in range(self.i0, self.i1):
            y_ = self.m * self.x[k] + self.b
            if np.abs(y_ - self.y[k]) > self.eps:
                return False
        return True


def taut_string(x, y, epsilon):
    '''Taut string fit to the data y = f(x).
    -----
    Here is how it works:
    '''
    T = len(x)
    breakpoints = []
    breakpoints.append(0) # indices corresponding to line breaks.
    line = Line(x, y, epsilon)
    y_ = []
    
    # Outer loop. Starting at current breakpoint, draw successively longer
    # lines until we violate the epsilon condition.
    go=True
    while go:
        cbp = breakpoints[-1]
        for idx in np.arange(cbp+1,T):
            line.fit(cbp, idx)
            if not line.valid or (idx==T-1):
                breakpoints.append(idx)
                y_ = np.append(y_, line.eval(x[cbp:idx]))
                if (idx == T-1):
                    y_ = np.append(y_, y[-1])
                    go = False
                break
    return y_, breakpoints 


if __name__ == '__main__':
    import pylab as plt
    import seaborn as sns
    from seaborn import xkcd_rgb as xkcd
    
    # Make some data.
    x = np.linspace(0,2*np.pi, 100)
    y = np.sin(2*np.pi/5*x) + 0.01 * np.random.randn(len(x))
    y_, bks = taut_string(x,y,0.2)

    # Plot that guy.
    plt.ion()
    plt.close('all')
    plt.plot(y)
    plt.plot(y_)


    # plt.figure()
    # plt.plot(y - y_)
