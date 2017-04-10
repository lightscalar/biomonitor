import numpy as np
from mathtools.fit import Fit
from mathtools.utils import Vessel
import pylab as plt
import seaborn as sns
from seaborn import xkcd_rgb as xkcd
from ipdb import set_trace as debug
from taut_string import *
from scipy.optimize import curve_fit
from scipy.signal import resample


def func(x, a, b, c):
    return a * np.exp(-b * x) + c


def euc(x,y):
    return np.sqrt(((x-y)**2).sum()) 


def taut(x, y, eps):
    '''Version of the taut string algorithm.'''
    n = len(x)

    # Normalize the data.
    x = np.array(x)
    y = np.array(y)
    x_ = np.linspace(0,1,n)
    y_ = (y - y.mean())/y.std()

    u = [0]
    can_add_point = True
    while can_add_point:
        last = u[-1]
        can_add_point = False
        x1 = x_[last]
        y1 = y_[last]
        p1 = np.array([x1,y1])
        for k in range(last,n):
            x2 = x_[k]
            y2 = y_[k]
            p2 = np.array([x2,y2])
            # print(euc(p1,p2)/eps)
            if euc(p1,p2) >= (3 * eps):
                u.append(k)
                can_add_point = True
                break
        fit_machine = Fit(x_[u], nb_bases=10)
        fit = fit_machine.fit(y_[u])
        fit = fit_machine.resample(x_)

    return fit, x_, y_, u


def feature(pulse):
    '''Extract the features from the pulse.'''
    v = pulse
    t_ = np.linspace(0,1,len(v))
    v /= v.max()

    md = np.median(v)
    half_max = (1+md)/2
    half_max_pos = np.nonzero( v <= half_max )[0][0]

    dilation_factor = 0.1/t_[half_max_pos]
    td = t_ * dilation_factor
    stretch_point = np.nonzero(td >= 0.2)[0][0]
    md = v[stretch_point]
    delta = (1-md)
    v -= md
    v /= delta
    return td, v


if __name__=='__main__':

    # Load the playing data.
    g = Vessel('playdata.dat')
    oset = g.peaks[35]
    dt = 300
    t,v = g.t[oset:oset+dt], g.v[oset:oset+dt]

    plt.ion()
    plt.close('all')

    sig = np.zeros((len(g.peaks), dt))
    for k, pk in enumerate(g.peaks):
        oset = pk
        t,v = g.t[oset:oset+dt], g.v[oset:oset+dt]
        td, sig[k,:] = feature(v)

        fitter = Fit(td, nb_bases=25)
        fit = fitter.fit(sig[k,:])

        plt.close(200)
        plt.figure(200)
        plt.plot(td, fit.d2y/fit.d2y.max())
        plt.plot(td, fit.y)
        plt.ylim([-1,1])
        plt.xlim([0,1])
        out = input()
        if (out == 'x'): break

    

