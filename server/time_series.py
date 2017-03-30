'''A nice object for efficiently storing time series data to disk.'''
import numpy as np
from mathtools.utils import Vessel
import logging
from time import sleep, time
from ipdb import set_trace as debug


class TimeSeries(object):

    def __init__(self, filename, autoflush=True, flush_interval=2000):

        # Initialize the Vessel-based store.
        self.filename = filename
        self.store = Vessel(self.filename)
        self._init_store()
        self.insert_counter = 0
        self.autoflush = autoflush
        self.flush_interval = flush_interval

        # Set up the logger.
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self.info = self.logger.info

    def _init_store(self):
        self.store = Vessel(self.filename)
        if 'series' not in self.store.keys:
            self.store.series = {}

    def insert(self, data):
        '''Insert data into the time series database.
        INPUT
            data - array_like
                Data to insert. Format is [CHANNEL_NB, TIMESTAMP, VALUE]
                These elements are assumted to be of type np.int32...
        '''
        chn = np.int32(data[0])
        if chn not in self.store.series:
            # Initialize the channel number for this series, if nonexistent.
            self.store.series[chn] = []
        self.store.series[chn].append((np.int32(data[1]), np.int32(data[2])))
        self.insert_counter += 1
        if np.mod(self.insert_counter, self.flush_interval) == 0:
            self.flush()

    def flush(self):
        '''Save the data to the disk'''
        start = time()
        self.info(' > Saving to disk.')
        self.store.save()
        self.insert_counter = 0
        self.info(' > Done in {:f}'.format(time()-start))


if __name__=='__main__':

    # Let's sample data at 400 Hz..
    f = 400
    dt = 1.0/f

    # Collect it to channel 0!
    channel_nb = 0
    timestamps = np.arange(0,10000, dtype='int32')
    ts = TimeSeries('03.ts', flush_interval=800)

    for t in timestamps:
        data = (channel_nb, t, np.random.randint(2**24-1, dtype='int32'))
        ts.insert(data)
        sleep(dt)

