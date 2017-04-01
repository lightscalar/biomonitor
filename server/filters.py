import seaborn
import pylab as plt
import numpy as np
from scipy.signal import butter, lfilter
from mathtools.utils import Vessel


def lowpass(t, y, filter_order=5, freq_cutoff=10, zi=[]):
    '''Lowpass Butterworth filter the signal.'''

    # Determine the sampling rate of the supplied data.
    fs = 1/np.median(np.diff(t))
    nyquist=0.5*fs
    f_low = freq_cutoff/nyquist

    # Create a butterworth filter
    a,b  = butter(filter_order, f_low, 'low', analog=False)

    # Check to see of previous filter delays are passed in.
    if len(zi) == 0:
        zi = np.zeros(filter_order)

    # Filter the actual signal
    y_filt, zf = lfilter(a, b, y, axis=-1, zi=zi)

    # Return BOTH filtered signal and updated tap delays.
    return y_filt.tolist(), zf.tolist()


if __name__ == '__main__':

    # Load some data. 
    v = Vessel('data/good_collection.dat')
    t = v.t * 1e-6
    y = v.y
    N = len(t)
    half = int(np.floor(N/2))

    t0 = t[0:half] 
    t1 = t[half+1:]

    y0 = y[0:half] 
    y1 = y[half+1:]

    filter_order = 4
    yf, zo = lowpass(t0, y0)
    # y0_filt,zi = lowpass(t0, y0, filter_order=filter_order, freq_cutoff=6)
    # y1_filt,zi = lowpass(t1, y1, filter_order, freq_cutoff=8, zi=zi)

    import pylab as plt
    plt.ion()
    plt.close('all')
    plt.figure(100)
    plt.plot(t0, yf)
    # plt.plot(t0, y0_filt)
    # plt.plot(t1, y1_filt)

