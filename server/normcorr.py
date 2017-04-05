
from numpy import *
from pylab import *
import pdb

# Define set of offsets k: 0,1,...2999
k = r_[0:3000]

# Define some spectral peaks (just some appropriately shifted Gaussians of various widths)
pk1 = 10*exp( -(k - 300)**2/(8**2) )
pk2 = 15*exp( -(k - 2300)**2/(15**2) )
pk3 = 15*exp( -(k - 1100)**2/(12**2) )

# Make our two synthetic spectra (white noise plus those peaks)
x = 0.5*randn(3000) + pk1 + pk2 # define first data set -- peaks at 300 & 2300
y = 0.5*randn(3000) + pk2 + pk3 # define second data set -- peaks at 1100 & 2300 

# Define the window width.
window_width = 150

# Let's EXPLICITLY compute the windowed correlation between these now. NOT OPTIMIZED! (but still fast)
rho = zeros(len(x))
iter = 0
# Loop over all window starting points
for ki in k:
	# Grab the points in the current window
	dx = x[ki:ki+window_width]
	dy = y[ki:ki+window_width]
	# Normalize these vectors
	dx = dx/norm(dx)
	dy = dy/norm(dy)
	# The dot product of these normalized vectors is the correlation!
	rho[iter] = dot(dx,dy)
	iter += 1

# Make some plots now.
close('all')
figure(1)
plot(x)
ylim([-15,15])
grid('on')
xlabel('Wave Number')
ylabel('Amplitude')
title('Spectrum 1')

figure(2)
plot(y,'r')
ylim([-15,15])
grid('on')
xlabel('Wave Number')
ylabel('Amplitude')
title('Spectrum 2')

figure(3)
title('Correlation | Window Width: %d' % window_width)
plot(rho[0:2995])
xlabel('Offset')
ylabel('Correlation')
grid()
xlim([0, 2999])

