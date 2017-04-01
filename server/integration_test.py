from pymongo import MongoClient
from database import connect_to_database 
from models import *
from device import *
import pylab as plt
import seaborn as sns
from filters import *
from mathtools.utils import Vessel


class Stream(object):
    '''Mock stream object. Minimal API.
    -----
        This is the minimal API for a stream process that can be read by the
        biomonitor board. The stream object must expose a channels attribute,
        as well as a time_series dictionary indexed by the physical channel
        number. The time_series must expose a .push(t,v) methods that accepts
        a timestamp, t, and and value, v. See Series, below, for more details.
    '''

    def __init__(self):
        self.time_series = {}
        self.time_series[1] = Series()


    @property
    def channels(self):
        return [1]
    

class Series(object):
    '''Mock time series object. Minimal API.
    ------
        Simplest possible time_series class. Exposes a .push method that
        stores the data in some in-memory lists.
    '''

    def __init__(self):
        self.t = []
        self.v = []


    def push(self, timestamp, value):
        self.t.append(timestamp)
        self.v.append(value)


if __name__ == '__main__':

    # This is it, folks. Open up the biomonitor. Read data to database.
    board = BioBoard()
    db = connect_to_database()
    
    # Create a new session to which we can stream data.
    session = {}
    session['name'] = 'Dialysis'
    channel = {'physical_channel':1, 'description': 'PVDF'}
    session['channels'] = [channel]
    s = SessionController(db, data=session)

    # START STREAMING DATA!!
    duration = 20
    board.start()               # start collecting from serial port
    board.stream_to(s)          # start writing to database via s
    sleep(duration)             # wait for a bit, collect some data
    board.stop_stream()         # stop writing
    board.kill()                # close serial connection

    # Load the series.
    t, v = s.time_series[1].series 

    # Plot some data for sanity purposes.
    plt.close('all')
    plt.ion()
    plt.figure(100)
    plt.plot(t, v)
    plt.ylim(0.05, 0.10)



