from analysis import *
from sig_proc import *
from mathtools import fit
import pylab as plt
import seaborn as sns
from seaborn import xkcd_rgb
from filters import *


if __name__ == '__main__':

    db = connect_to_database()
    sess_1 = 'Timing'
    s1 = grab_session(session_name=sess_1)
    # segment_size = s1.time_series[1].model['segment_size']
    t,v = s1.time_series[1].series
    t = np.array(t)
    v = np.array(v)
    t_,v_ = downsample(t,v,100)

    plt.ion()
    plt.figure()
    plt.plot(t,v)
    plt.plot(t_,v_)

    # f = Fit(t, nb_bases=51, basis_type='legendre')
    # fit = f.fit(v)
    # t_ = np.arange(np.min(t), np.max(t), 0.01)
    # fit_r = f.resample(t_) 


