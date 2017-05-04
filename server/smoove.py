import numpy as np
from mathtools.fit import Fit
from mathtools.utils import Vessel
import pylab as plt
import seaborn as sns
from seaborn import xkcd_rgb as xkcd
from ipdb import set_trace as debug
from taut_string import *


def func(x, a, b, c):
    return a * np.exp(-b * x) + c


def euc(x,y):
    return np.sqrt(((x-y)**2).sum()) 


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
    g = Vessel('chl_data.dat')
    oset = g.peaks[35]
    dt = 300
    t,v = g.t[oset:oset+dt], g.v[oset:oset+dt]

    plt.ion()
    plt.close('all')

    sig = np.zeros((len(g.peaks), dt))
    for k, pk in enumerate(g.peaks):
        oset = pk
        t,v = g.t[oset:oset+dt], g.v[oset:oset+dt]
        td, vd = feature(v)
        taut = taut_string(vd, 0.05)

        idx = (td<0.6)
        ftr = taut[idx]

        metric = vd[idx] - ftr
        try:
            metric -= np.min(metric)
            metric *= 10
        except:
            pass

        # Integrate area under the curve between 0.15 and 0.5.
        t_int = np.nonzero((td>0.15) * (td<0.5))
        delta_t = np.median(np.diff(t))
        area = delta_t * sum(metric[t_int])

        plt.close(200)
        plt.figure(200)
        plt.subplot('211')
        plt.plot(td[idx], vd[idx])
        plt.plot(td[idx], ftr)
        plt.ylim([-1,1])
        plt.xlim([0,0.6])
        plt.subplot('212')
        plt.plot(td[idx], metric, label='{:0.2f}'.format(area))
        plt.legend(loc=0)
        plt.ylim(0,1)
        out = input()
        if (out == 'x'): break

    

