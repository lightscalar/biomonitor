from pymongo import MongoClient
from database import connect_to_database 
from models import *
from device import *
import pylab as plt
import seaborn as sns


class Stream(object):
    '''Mock stream object. Minimal API.'''

    def __init__(self):
        self.time_series = {}
        self.time_series[1] = Series()

    @property
    def channels(self):
        return [1]
    

class Series(object):
    '''Mock series object. Minimal API.'''

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
    
    session = { 'name':'Dialysis', 
                'channels': [{'physical_channel': 1,
                'description': 'PVDF Sensor'}]}
    s = SessionController(db, data=session)

    # Create a mock stream.
    obj = Stream()

    board.start()               # start collecting from serial port
    sleep(1)                    # give 'er time to connect 
    board.stream_to(obj)        # start writing to database
    sleep(3)                    # wait for a bit, collect some data
    board.stop_stream()         # stop writing
    board.kill()                # close serial connection

    # Note that if the board never connects, we'll have no data!
    t = np.array(obj.time_series[1].t)
    v = np.array(obj.time_series[1].v)

    # Plot some data for sanity purposes.
    plt.close('all')
    plt.ion()
    plt.figure(100)
    plt.plot(t, v)
       



