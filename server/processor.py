import numpy as np
import pylab as plt
from ipdb import set_trace as debug
from database import *
from models import *
from mathtools.fit import Fit
from taut_string import *
import seaborn as sns
from seaborn import xkcd_rgb
from mathtools.utils import mahal
from scipy.signal import resample
from filters import *
sns.set_context('talk')
plt.ion()
plt.close('all')


def dex(booleans):
    '''Convenience function for returning indices satisfying a boolean.'''
    return np.nonzero(booleans)[0]


def grab_session(session_name='MJL.VSM'):
    '''Grab a session from the database.'''
    db = connect_to_database()
    session = db.sessions.find_one({'name': session_name})
    return SessionController(db, _id=session['_id'])


def find_peaks(t, v):
    '''Extract pressure wave pulses from the time series.'''

    v = np.array(v)
    t = np.array(t)
    minf = np.median(v)
    maxf = v.max()

    depths = np.linspace(minf, maxf, 500)
    metric = []
    for d in depths:
        idx = np.nonzero(v>d)[0]
        metric.append(len(idx))
        
    m = np.cumsum(metric)/sum(metric)
    # mx = np.linspace(0,1,len(m))
    
    # fit = Fit(mx, nb_bases=25, reg_coefs=[0,1e-3,1e-3])
    # ft = fit.fit(m)

    # Extract the derivatives.
    # dy = ft.dy
    # d2y = ft.d2y
 
    # Find the break in the curve (where curvature, i.e. second derivative
    # is the highest.
    # winner = np.argmax(abs(ft.d2y)) + 100
    # Winner is the first element less than 90% of cumsum.
    winner = dex(m<0.85)[-1]
    depth = depths[winner]

    idx = np.nonzero(v>depth)[0] 
    df = np.diff(idx)

    # Find cluster breaks; partition peak clusters.
    cluster_breaks = np.nonzero(df>50)[0]+1
    clusters = []
    k = 0
    for next_k in cluster_breaks:
        clusters.append(idx[k:next_k])
        k = next_k

    # Identify the indices at the peaks of the clusters.
    peak_indices = []
    peak_height = []
    for cluster in clusters:
        cluster_argmax = np.argmax(v[cluster])
        if (len(v) - cluster[cluster_argmax])>600:
            peak_indices.append(cluster[cluster_argmax])

    return np.array(peak_indices)


def scan_for_peaks(t, v, dt=3):
    '''Scan through data in increments of dt to find peaks.'''
    if len(t) == 0:
        return []
    t_ = 1.0 * t
    t_ -= t_[0]
    maxt = t_.max()
    tot_increments = int(2*maxt/dt)
    peaks = []
    for k in range(tot_increments):
        i_ = dex((t_>=k*dt/2) * (t_<k*dt/2+dt))
        start_idx = i_[0]
        t_sub = t_[i_]
        v_sub = v[i_]
        peaks += list(find_peaks(t_sub, v_sub) + start_idx)

    # Clean up the peaks. Peaks that are too close together should be
    # discarded.
    peaks = np.unique(peaks)
    dpks = np.diff(peaks)
    mdp = np.median(dpks)
    std = np.std(dpks)
    z_scores = (dpks - mdp)**2/std**2
    i_ = dex(z_scores>1.0)
    discard = []

    # Find all peaks that are too close, statistically speaking.
    for peak_idx in i_:
        if v[peaks[peak_idx]] > v[peaks[peak_idx+1]]:
            discard.append(peaks[peak_idx+1])
        else:
            discard.append(peaks[peak_idx])

    # Discard the smaller of the two nearby peaks.
    for peak in discard:
        i_ = dex(peak == peaks)
        peaks= np.delete(peaks, i_)
    
    return peaks


def extract_pulses(t,v,peaks):
    '''Extract pulses from the time series, given peaks.'''

    # Find the median pulse width. We only want first half.
    pulse_width = int(np.median(np.diff(peaks))/2)
    pulses = np.zeros((len(peaks), pulse_width)) 
    times = np.zeros((len(peaks), pulse_width))

    for k, peak in enumerate(peaks):
        pulses[k,:] = v[peak: peak+pulse_width]
        times[k,:]  = t[peak: peak+pulse_width]

    return times, pulses


def filter_pulses(pulses, thresh_factor=1.0):
    '''Use Mahalanobis distance to filter pulses for quality.'''
    # d = np.sqrt(mahal(pulses))
    median_pulse = np.median(pulses)
    dp = pulses - median_pulse
    dp = np.sum(dp**2,1)
    z_score = np.abs(dp - dp.mean(0))/dp.std(0)
    keepers = dex((z_score) < thresh_factor)
    if len(keepers) == 0:
        best = np.argsort(z_score)
        keep_nb = np.min(2,len(best))
        keepers = best[0:keep_nb]
    return pulses[keepers,:]


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
    t_final = np.linspace(0,1,200)
    fitter = Fit(td, nb_bases=75)
    f = fitter.fit(v)
    f = fitter.resample(t_final)
    return t_final, f.y


def estimate_bpm(t,v):
    '''Estimate heart rate from time series data.'''
    peaks = scan_for_peaks(t,v,dt=3)
    bpm = 60/(np.median(np.diff(t[peaks])))

    return bpm


def golden_representation(t,v):
    '''Find peaks; extract features; filter; return the mean.'''
    peaks = scan_for_peaks(t,v,dt=3)
    times, pulses = extract_pulses(t, v, peaks)
    clean_pulses = filter_pulses(pulses)
    fpulses = []
    for k, pulse in enumerate(clean_pulses):
        try:
            tf, fp = feature(pulse)
            fpulses.append(fp)
        except:
            pass

    # Stack these guys up.
    fpulses = np.vstack(fpulses)

    # Compute the mean pulse.
    the_pulse = np.median(fpulses,0)
    fitter = Fit(tf, nb_bases=50, reg_coefs=[0,1e-3,1e-3])
    f = fitter.fit(the_pulse)
    the_pulse = f.y

    i_ = dex(tf<0.60)

    taut = taut_string(the_pulse, 0.05)
    taut = taut
    resid = the_pulse - taut
    resid = resid[i_]
    resid -= resid.min()
    resid *= 10
    t_resid = np.linspace(0,1,len(i_))
    a_ = dex((t_resid>0.3) * (t_resid<0.7))
    area = resid[a_].sum() * np.median(np.diff(t_resid))

    # Normalized score, for the moment.
    score = np.min([400*area,100])

    return the_pulse, resid, t_resid, score


if __name__ == '__main__':

    sess_1 = 'May 10c'
    # sess_1 = 'DUAL 14'
    # sess_1 = 'APR.18_3'
    s1 = grab_session(session_name=sess_1)
    t, v = s1.time_series[1].series
    t = np.array(t)
    v = np.array(v)
    # v,z = lowpass(t,v)

    peaks = scan_for_peaks(t,v, dt=3)

    plt.figure(100, figsize=(13,5))
    plt.plot(t,v)
    plt.plot(t[peaks], v[peaks], 'o', color=xkcd_rgb['dusty rose'])
    plt.xlabel('Time (seconds)')
    plt.ylabel('PVDF Signal (volts)')
    plt.xlim([37,43])
    plt.ylim([0.05, 0.15])
    plt.savefig('plots/peak_finder.png')

    st1 = 80
    st2 = 70
    delta= 30
    i_1 = dex((t>st1-delta) * (t<st1+delta))
    i_2 = dex((t>st2-delta) * (t<st2+delta))

    t1 = t[i_1]
    v1 = v[i_1]
    t2 = t[i_2]
    v2 = v[i_2]

    p1, r1, tr, area1 = golden_representation(t1, v1)
    p2, r2, tr, area2 = golden_representation(t2, v2)
    
    plt.figure(200, figsize=(7,8))
    plt.plot(tr, p1[:len(tr)], label='Time t = 20 sec')
    plt.plot(tr, p2[:len(tr)], label='Time t = 40 sec')
    plt.xlabel('Time (seconds)')
    plt.ylabel('Normalized Pulse Amplitude')
    plt.title('Golden Pulse Extraction $\pm 20$ seconds')
    plt.legend(loc=0)
    plt.savefig('plots/golden_pulse.png')

    plt.figure(300)
    plt.plot(tr, r1, label='{:0.2f}'.format(area1))
    plt.plot(tr, r2, label='{:0.2f}'.format(area2))
    plt.xlabel('Time (seconds)')
    plt.ylabel('Residual Features')
    plt.title('Residual Reflection Feature $\pm 20$ seconds')
    plt.legend(loc=0)
    plt.legend(loc=0)
    plt.savefig('plots/residuals.png')

    bpm_ = estimate_bpm(t,v)
    
    if False:
        delta = 20 # seconds
        scores = []
        for t_ctr in np.linspace(0, np.min([150, t.max()]), 50):
            print(t_ctr)
            
            # Scan through all the data.
            i_ = dex((t>t_ctr-delta) * (t<t_ctr+delta))
            t_ = t[i_]
            v_ = v[i_]
            p1, r1, tr, score = golden_representation(t_, v_)
            scores.append(score)

        # Plot the score metric over time.
        plt.figure(100)
        plt.plot(np.linspace(0,t.max(), 50),scores)

            
