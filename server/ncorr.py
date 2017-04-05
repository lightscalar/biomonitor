### implementation of normalized correlation
#import scipy
#from scipy import *
#from scipy.fftpack import *

from scipy import *
from pylab import *

# this one is cyclical version
def ncorr_cyclical(needle,haystack):
    L = len(needle)
    N = len(haystack)

    pad_needle = zeros(N,dtype='double')
    pad_X = zeros(N,dtype='double')
    pad_X[0:L] = 1.0

    pad_needle[0:L] = needle

    norm_needle = sqrt((needle.conjugate()*needle).sum())
    HH = haystack.conjugate()*haystack

    Fneedle = fft(pad_needle)
    Fhaystack = fft(haystack)
    FX = fft(pad_X)
    mag_needle = sqrt((needle.conjugate()*needle).sum())
    FHH = fft(HH)

    Cnum = real(ifft(Fhaystack*(Fneedle.conjugate())))
    Cden = mag_needle*sqrt(real(ifft(FHH*(FX.conjugate()))))
    
    #1/0
    C = Cnum/Cden
    return C

# this one is cyclical version
def ncorr_cyclical2(f,g):
    L = len(f)
    N = len(g)

    hf = zeros(N,dtype='double')
    hg = zeros(N,dtype='double')
    hX = zeros(N,dtype='double')

    Cnum = zeros(N,dtype='double')
    Cden = zeros(N,dtype='double')

    hf[0:L] = f/sqrt((f.conjugate()*f).sum())
    hg = 1.0*g
    hX[0:L] = 1.0


    fhf = fft(hf)
    fhg = fft(hg)
    fhX = fft(hX)
    fhg2 = fft(g.conjugate()*g)
    
    Cnum = ifft(fhf.conjugate()*fhg)
    Cden = sqrt(real(ifft(fhX.conjugate()*fhg2)))

    C = Cnum/Cden
    return C

# normalized cross correlation of needle:f with haystack:g
def ncorr(f,g):

    L = f.shape[0] 
    N = g.shape[0]
    P = L+N-1

    hf = zeros(P)
    hg = zeros(P)
    X = zeros(P)
    hX = zeros(P)
    hag2 = zeros(P)
    Cnum = zeros(P)
    Cden = zeros(P)
    C = zeros(P)

    ### temporarily "size" data
    hf[0:L] = f[0:L];
    # hg[L:N+L] = g[0:N] # if want the ramp up in the front
    hg[0:N] = g[0:N] # if want to look for the location of x in y

    ### set up support (indicator) function (allows for performations)
    suppIdx = nonzero(hf != 0.0)
    X = zeros(P)
    X[suppIdx] = 1.0
    # X[0:L] = ones(L); # use this if want full domain of f

    ### get transforms
    hf = fft(hf)
    hag2 = fft(hg*conj(hg))
    hg = fft(hg)
    hX = fft(X)

    Cnum = conj(ifft(conj(hf)*hg))
    Cden = sqrt(dot(f,conj(f)))*sqrt(ifft(hag2*conj(hX)))

    C = Cnum/Cden

    return real(C)

# example...
if __name__ == '__main__':
    ion()
    Nhaystack = 1000
    Nneedle = 10

    needle = randn(Nneedle)
    haystack = randn(Nhaystack)
    noise = 0.1*randn(Nhaystack)

    itruth = int((Nhaystack-Nneedle)*rand())

    haystack[itruth:itruth+Nneedle] = needle

    cc = ncorr(needle,haystack+noise)
    imax = argmax(abs(cc))

    figure(10);clf()
    hold(True)
    plot(cc,'-b.');grid(True)
    title('ncorr %d / %d'%(itruth,imax))
    
    ccc = ncorr_cyclical(needle,haystack+noise)
    imaxc = argmax(abs(ccc))

    figure(11);clf()
    hold(True)
    plot(ccc,'-b.');grid(True)
    title('ncorr- cyclical- %d / %d'%(itruth,imaxc))

    
