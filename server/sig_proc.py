import numpy as np


def downsample(t, x, target_sampling_rate):
    '''Smarter downsampling. We now pad out to appropriate length, and average
       samples appropriately in order to approximately achieve the target
       downsampling rate.
    '''

    if len(t) == 0:
        # Nothing to downsample. So, um. Sort of awkward.
        return t, x

    # Convert to numpy arrays.
    t, x = np.array(t), np.array(x)

    # Estimate current sampling rate.
    fs = 1/np.median(np.diff(t))

    # Calculate the downsample factor, given the target sampling rate.
    R = int(np.ceil(fs/target_sampling_rate))

    # Determine the padding size & pad the data.
    padsize = int(np.ceil(len(x)/R)*R - len(x))
    t = np.append(t, np.zeros(padsize)*np.NaN)
    x = np.append(x, np.zeros(padsize)*np.NaN)

    # Reshape the data.
    x = x.reshape(-1, R)
    t = t.reshape(-1, R)

    # Take the mean along axis 1 and convert back to list. Et voila!
    x_ = list(np.nanmean(x, 1))
    t_ = list(np.nanmean(t, 1))

    return t_, x_
    




