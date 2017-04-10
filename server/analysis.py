import numpy as np
import pylab as plt
import seaborn as sns
from seaborn import xkcd_rgb as xkcd
from mathtools.fit import Fit
from scipy.signal import resample
from database import *
from models import *
from ncorr import *
from mathtools.utils import mahal
from ipdb import set_trace as debug
from scipy.cluster.vq import kmeans2


def downsample(t, y, sampling_rate=200):
    '''Downsample signal y to target sampling rate.'''
    dt = np.max(t) - np.min(t)
    nb_samples = int(dt*sampling_rate)
    y_,t_ = resample(y, nb_samples, t=t)
    return (t_, y_) 


def grab_session(session_name='MJL.VSM'):
    # .002 is a great session!
    db = connect_to_database()
    session = db.sessions.find_one({'name': session_name})
    return SessionController(db, _id=session['_id'])


class FeatureExtractor(object):

    def __init__(self, t, f, feature_dim=25):

        # Save the current data into the object.
        self.t = np.array(t)
        self.v = np.array(v)

        # Extract all available pulses.
        self.extract_pulses()
        self.evaluate_pulses()
        self.compute_gold()


    def extract_pulses(self):
        '''Extract pressure wave pulses from the time series.'''

        minf = np.median(self.v)
        maxf = self.v.max()

        depths = np.linspace(minf, maxf, 500)
        metric = []
        for d in depths:
            idx = np.nonzero(self.v>d)[0]
            metric.append(len(idx))
            
        m = np.cumsum(metric)
        mx = np.linspace(0,1,len(m))
        
        fit = Fit(mx, nb_bases=25, reg_coefs=[0,1e-3,1e-3])
        ft = fit.fit(m)

        # Extract the derivatives.
        dy = ft.dy
        d2y = ft.d2y
     
        # Find the break in the curve (where curvature, i.e. second derivative
        # is the highest.
        winner = np.argmax(abs(ft.d2y))
        depth = depths[winner]

        idx = np.nonzero(self.v>depth)[0] 
        df = np.diff(idx)

        # Find cluster breaks; partition peak clusters.
        cluster_breaks = np.nonzero(df>50)[0]+1
        clusters = []
        k = 0
        for next_k in cluster_breaks:
            clusters.append(idx[k:next_k])
            k = next_k

        # Identify the indices at the peaks of the clusters.
        self.peak_indices = []
        self.peak_height = []
        for cluster in clusters:
            cluster_argmax = np.argmax(self.v[cluster])
            if (len(self.v) - cluster[cluster_argmax])>600:
                self.peak_indices.append(cluster[cluster_argmax])
                self.peak_height.append(np.max(self.v[cluster]))

        dpk = median(diff(self.peak_indices))
        clean_peaks = []
        for k, pki in enumerate(self.peak_indices):
            if k>0 and (k<len(self.peak_indices)-1):
                pkh = self.peak_height[k]
                smaller_than_prev = (pkh<self.peak_height[k-1])
                smaller_than_next = (pkh<self.peak_height[k+1])
                df_surround = self.peak_indices[k+1] - self.peak_indices[k-1]
                df_good = (abs(df_surround - dpk) < 50)
                if not (df_good * smaller_than_next * smaller_than_prev):
                    clean_peaks.append(pki)
        self.peak_indices = clean_peaks

        # Grab the highest peaks.
        # clean_peaks = []
        # nb_clusters = 2
        # vals, classes = kmeans2(self.peak_height,nb_clusters,iter=100)
        # if len(np.unique(classes)) == nb_clusters:
        #     keepers = np.argsort(vals)[-(nb_clusters-1):]
        #     clean_peaks = []
        #     for k, loc in enumerate(self.peak_indices):
        #         if (classes[k] in keepers):
        #             clean_peaks.append(loc)
        #     self.peak_indices = clean_peaks

    
        # Find the median pulse width.
        # median_pulse = int(median(diff(self.peak_indices)))
        median_pulse = 200
        self.median_pulse = median_pulse
        x = linspace(0,1,median_pulse) 
        self.fitter = Fit(x, nb_bases=20, reg_coefs=[0,1e-2,1e-3])
        self.fits = []
        self.coefs = []
        self.pulses = []
        for k, pki in enumerate(self.peak_indices):

            pulse = 1.0 * self.v[pki:pki+median_pulse]
            pulse -= pulse.mean()
            pulse /= pulse.std()
            self.pulses.append(pulse)
            self.fits.append(self.fitter.fit(pulse))
            self.coefs.append(self.fits[k].coefs)

        # Turn these guys into an nd.array.
        self.coefs = np.vstack(self.coefs)


    def evaluate_pulses(self):
        '''Characterize the distribution of pulses.'''
        
        # Calculate the Mahalanobis distance of the coefficients.
        self.mahal_dist = mahal(self.coefs)

        # Take the core pulses (lower half) and recompute Mahalanobis
        # distances.
        best_pulses = argsort(self.mahal_dist)[:int(self.nb_pulses/2)]
        self.golden_mu = self.coefs[best_pulses,:].mean(0)
        self.golden_cov = self.coefs[best_pulses,:].T.\
                dot(self.coefs[best_pulses,:])
        mahal_next = mahal(self.coefs, self.golden_mu, self.golden_cov)
        best_pulses_2 = argsort(mahal_next)
        self.golden_coefs = median(self.coefs[best_pulses_2,:],0)
        self.bp2 = best_pulses_2
        self.bp1 = best_pulses
        self.pulse_quality = exp(-mahal_next/(2*self.coefs.shape[1]))*100


    def compute_gold(self):
        '''Construct golden quantities.'''
        self.golden_pulse = self.fitter.basis.B.dot(self.golden_coefs)
        self.residuals = []
        for pulse in self.pulses:
            gx = np.linspace(0,1,len(self.golden_pulse))
            smooth_fit = Fit(gx, nb_bases=10, reg_coefs=[0,1e-2,1e-1])
            pfit = smooth_fit.fit(1.0*pulse)
            resid = pulse - pfit.y
            resid -= resid.mean()
            resid /= resid.std()
            self.residuals.append(resid)

        self.gold_residuals = []  
        self.gold_coefs = []
        self.gold_pulses = []
        max_gold = 15
        for k in range(max_gold):
            self.gold_residuals.append(self.residuals[self.bp2[k]])
            self.gold_coefs.append(self.coefs[self.bp2[k]])
            self.gold_pulses.append(self.pulses[self.bp2[k]])

        # Stack things up.
        self.gold_residuals = np.vstack(self.gold_residuals)
        self.gold_coefs = np.vstack(self.gold_coefs)

        # vecfit = Fit(gx, nb_bases=25, reg_coefs=[0,1e-3,-1e3])
        # vfit = vecfit.fit(self.gold_residuals.mean(0))
        # self.fvec = vfit.coefs
        # COMPUTE FEATURE VECTOR.
        self.fvec = self.gold_coefs.mean(0)
        self.fvec /= np.linalg.norm(self.fvec)
        self.gold_pulses = np.vstack(self.gold_pulses)
        self.pulses = np.vstack(self.pulses)


    @property
    def nb_pulses(self):
        '''Returns the number of pulses discovered.'''
        return len(self.pulses)

    
if __name__=='__main__':
    plt.ion()
    plt.close('all')
    
    # Grab data from two different sessions.
    sess_1 = 'MJL.N02'
    s1 = grab_session(session_name=sess_1)
    t,v = s1.time_series[1].series
    f1 = FeatureExtractor(t,v)

    sess_2 = 'MJL.V01'
    s2 = grab_session(session_name=sess_2)
    t,v = s2.time_series[1].series
    f2 = FeatureExtractor(t,v)

    plt.ion()
    plt.close('all')

    plt.figure(100)
    plt.plot(f1.gold_residuals.T, color=sns.xkcd_rgb['blue'], alpha=0.1)
    plt.plot(f2.gold_residuals.T, color=sns.xkcd_rgb['red'], alpha=0.1)
    plt.plot(f1.gold_residuals.mean(0), color=sns.xkcd_rgb['blue'], label=sess_1)
    plt.plot(f2.gold_residuals.mean(0), color=sns.xkcd_rgb['red'], label=sess_2)
    legend()
    title('Residuals')
    savefig('plots/resids.png')

    plt.figure(200)
    # plt.plot(f1.gold_coefs.mean(0), '-o', label=sess_1)
    # plt.plot(f2.gold_coefs.mean(0), '-o', label=sess_2)
    plt.plot(f1.fvec, '-o', label=sess_1)
    plt.plot(f2.fvec, '-o', label=sess_2)
    prob = f1.fvec.dot(f2.fvec)**4 * 100
    title('Match index is {:.2f}'.format(prob))
    legend()
    savefig('plots/matches.png')

    plt.figure(300)
    plt.plot(f1.gold_pulses.T, color=sns.xkcd_rgb['blue'], alpha=0.1)
    plt.plot(f2.gold_pulses.T, color=sns.xkcd_rgb['red'], alpha=0.1)
    plt.plot(f1.gold_pulses.mean(0), color=sns.xkcd_rgb['blue'], label=sess_1)
    plt.plot(f2.gold_pulses.mean(0), color=sns.xkcd_rgb['red'], label=sess_2)
    legend()
    title('Pulses')
    savefig('plots/pulses.png')

    # plt.figure(350)
    # plt.plot(f1.gold_re)

    # plt.figure(400)
    # pn = 23
    # nfigs = 5
    # # pulses = [458, 135, 440, 436, 331, 301, 330, 319, 303]
    # pulses = [1, 2, 56, 47, 46, 50, 49, 35, 34, 14, 0]
    # for pn in pulses:
    #     if f1.pulse_quality[pn]>90:
    #         p = f1.pulses[pn]
    #         plt.plot(p, color=sns.xkcd_rgb['blue'], label='{:.1f}'.format(f1.pulse_quality[pn]))
    #     else:
    #         p = f1.pulses[pn]
    #         plt.plot(p, color=sns.xkcd_rgb['red'], label='{:.1f}'.format(f1.pulse_quality[pn]))
    # legend(loc=0)
    # title('Sample Pulse Quality Measures')

    sns.set_context('talk')
    plt.figure(500, figsize=(15,8))
    plt.plot(f1.t, f1.v)
    plt.plot(f1.t[f1.peak_indices], f1.v[f1.peak_indices], 'ro',\
             label='Peak Detected')
    # xlim([6,12])
    xlabel('Time (s)')
    ylabel('PVDF Signal (V)')
    # # savefig('plots/peak_finder_.png')

