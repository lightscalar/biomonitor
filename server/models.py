from pymongo import MongoClient
from database import *
import logging as log
from ipdb import set_trace as debug
from filters import lowpass


class ModelController(object):

    def __init__(self, model_name, database, data=None, _id=None,\
            verbose=log.INFO):

        # We have ourselves a database.
        self.db = database
        self.model_name = model_name
        self.collection = self.db[model_name]
        self.sideload = {}

        # Set up logging.
        log.basicConfig(level=verbose)
        self.log = log.getLogger(__name__)

        if (data is None) and (_id is None):
            # If nothing is specified, let's load all session models!
            self._list()

        if (data is not None):
            # Default is to create a new session.
            data['created_at'] = created_at()
            self.create(data)

        if (_id is not None):
            # Attempt to look up the session given the id.
            self._id = _id
            self.read()


    def _read(self):
        '''Find a specific model given its _id.'''
        self.model = self.collection.find_one(qwrap(_id))


    def _list(self):
        '''Return a collection of all models in the database.'''
        self.models = list(self.collection.find())
        return self.models


    def _create(self, data):
        '''Create a new model in the database. Call this for core update.'''
        if self.validate(data):
            self.log.info(' > Attempting to create a new model in {:s}'.\
                    format(self.model_name))
            try:
                insertion = self.collection.insert_one(data)
            except:
                self.log.exception(' > Critical error in creating {:s}.'.\
                        format(self.model_name))
            self.log.info(' > Created a new model in {:s}'.format(self.\
                    model_name))
            self.model = find_inserted_document(insertion, self.collection)
            self._id = self.model['_id']
            return self.model


    def create(self, data):
        '''Override this method as necessary. Calls the core _create method.'''
        session = self._create(data)
        

    def validate(self, data):
        '''Ensure the proposed object has required fields.'''
        for attribute in self.required_attributes:
            if attribute not in data:
                raise ValueError('Field "{:s}" is not present in data.'.\
                        format(attribute))
        return True


    def _update(self):
        '''Saves the current model to the database.'''
        self.log.info(' > Updating current model in {:s}'.format(self.\
                model_name))
        self.collection.update_one(qry(self.model), {'$set': self.model})


    def _read(self):
        '''Retrieve the core model from the database.'''
        self.model = self.collection.find_one(qwrap(self._id))
        self._id = self.model['_id']


    def _delete(self):
        '''Delete the core model from the database.'''
        self.collection.delete_one(qry(self._id))

    @property
    def required_attributes(self):
        return []


class SessionController(ModelController):
    '''Handle session creation, updating, and so on.'''

    def __init__(self, database, data=None, _id=None):
        '''Initialize the model as a sessions object.'''
        ModelController.__init__(self, 'sessions', database, data=data,\
                _id=_id)


    def read(self):
        '''Read a specific session from the database.'''
        self._read()
        self.load_series()


    def load_series(self):
        '''Add channel TimeSeries objects to dictionary indexed by physical
           channel.'''
        # Loop over the declared channels.
        self._series = {}
        for channel in self.model['channels']:

            # What is the physical channel number?
            phys_chan = channel['physical_channel']
            query = {'owner': self._id, 'physical_channel': phys_chan}
            
            # Find time series corresponding to the channel.
            series_id = self.db.time_series.find_one(query, {'_id':1})
            self._series[phys_chan] = TimeSeriesController(self.db,\
                                                           _id=q(series_id))

    def create(self, data):
        '''Create a new data session.'''
        self._create(data)

        # Add a time series for each channel in the session.
        for channel in self.model['channels']:
            # Create a new time series for each channel.
            channel['owner'] = self._id
            ts = TimeSeriesController(self.db, data=channel)
        self.load_series()


    @property
    def time_series(self):
        return self._series


    @property
    def channels(self):
        '''Expose the channel keys.'''
        return self.time_series.keys()


class TimeSeriesController(ModelController):
    '''Model time series data. Handle segment creation, filtering, etc.'''

    def __init__(self, database, data=None, _id=None):
        ModelController.__init__(self, 'time_series', database, data=data,\
                _id=_id)


    def read(self):
        '''Read the current time series from the database.'''
        self._read()
        self.load_segment()


    @property
    def series(self):
        '''Synthesize entire series from the available segments.'''
        # Initialize time and value lists.
        t,v = [],[]
        segments = self.db.segments
        cursor = segments.find({'owner':self._id, 'is_flushed':True},\
                               {'vals':1, 'time':1}).\
                               sort('min_time', 1)
        # Concatenate segments.
        for seg in cursor:
            v += seg['vals']
            t += seg['time']
        return (t, v)


    def load_segment(self):
        '''Load the latest segment.'''
        latest = self.db.segments.\
                find({'owner':self._id}, {'_id':1}).\
                sort([('created_at', -1)]).\
                limit(-1).next()

        # Assign current segment as attribute on this time series.
        self.segment = SegmentController(self.db, _id=q(latest))


    def create(self, data):
        # Create the time series object.
        data['segment_size'] = 1024
        data['freq_cutoff'] = 10
        data['filter_order'] = 5
        data['filter_coefs'] = []
        self._create(data)
        self.add_segment()


    def add_segment(self, current_segment=None):
        '''Add a new segment to the data series.'''
        segment_data = {}
        segment_data['owner'] = self._id
        segment_data['segment_size'] = self.model['segment_size']
        segment = SegmentController(self.db, data=segment_data)
        self._update()
        self.load_segment()


    @property
    def required_attributes(self):
        '''We need these guys to do anything useful.'''
        return ['owner', 'description', 'physical_channel']


    def push(self, timestamp, value):
        '''Push a new value into the time series.'''

        if self.segment.is_full:
            # Need to flush this segment to disk and start anew.
            self.filter_segment() # butterworth filter this guy.
            self.segment.flush()
            self.add_segment() 

        # Otherwise keep stuffing data in there.
        self.segment.push(timestamp, value)


    def filter_segment(self):

        # For convenience!
        t = self.segment.model['time']
        y = self.segment.model['vals']

        # Set parameters of the filter.
        order = self.model['filter_order']
        freq = self.model['freq_cutoff']
        coefs = self.model['filter_coefs']
        
        # Filter segment; store filter coefficients in time series.
        y_filt, coefs = lowpass(t, y, freq_cutoff=freq, filter_order=order,\
                                zi=coefs) 

        # Update the models.
        self.model['filter_coefs'] = coefs
        self.segment.model['filtered'] = y_filt
        
        # Fast updates of time series and the segment.
        self.db.time_series.update_one(qwrap(self._id),\
                {'$set':{'filter_coefs': coefs}})
        self.db.segments.update_one(qwrap(self.segment._id),\
                {'$set':{'filtered': y_filt}})

        # NOTE: BELOW IS SIMPLER, BUT SLOWER?
        # self._update()
        # self.segment._update()
         

class SegmentController(ModelController):

    def __init__(self, database, _id=None, data=None):

        if (_id is None): # initialize segment
            data = self.init_new_segment(data)
        ModelController.__init__(self, 'segments', database, _id=_id,\
                data=data)


    def read(self):
        '''Return database object.'''
        self._read()


    def init_new_segment(self, data):
        data['itr'] = 0
        data['min_time'] = 0
        data['max_time'] = 0
        data['time'] = list(np.zeros(data['segment_size']))
        data['vals'] = list(np.zeros(data['segment_size']))
        data['filtered'] = list(np.zeros(data['segment_size']))
        data['is_flushed'] = False
        if '_id' in data: del data['_id']
        return data


    @property
    def is_full(self):
        '''Are the time/value buffers at capacity?'''
        return (self.model['itr'] > self.model['segment_size'])


    def flush(self):
        '''Flush current segment to the disk. Load new segment into object.'''

        # Flush segment to the database.
        self.model['is_flushed'] = True
        self._update()


    def push(self, timestamp, value):
        '''Push an observation into the segment.'''

        # Update the time limits.
        if self.model['min_time'] == 0:
            self.model['min_time'] = timestamp
        if timestamp > self.model['max_time']:
            self.model['max_time'] = timestamp

        # Increment pointer.
        itr = self.model['itr']
        self.model['itr'] += 1

        # Insert element at appropriate place!
        if not self.is_full:
            self.model['time'][itr] = timestamp
            self.model['vals'][itr] = value


    @property
    def vals(self):
        return self.model['vals']


    @property
    def time(self):
        return self.model['time']


    @property
    def min_time(self):
        return self.model['min_time']


    @property
    def max_time(self):
        return self.model['max_time']


    @property
    def duration(self):
        return (self.model['max_time'] - self.model['min_time'])


if __name__=='__main__':

    # Connect to the database.
    database = connect_to_database()

    if True: 
        session = {'name':'Dialysis', 'channels': [{'physical_channel': 1,\
                'description': 'PVDF Sensor'}]}
        s = SessionController(database, data=session)

        # Simulate a data collection.
        duration = 5
        sampling_rate = 500 # Hz
        sampling_dt = 1/sampling_rate
        start = time.time()
        while (time.time() - start) < duration:
            value = np.random.randint(2**24-1)
            t = unix_time_in_microseconds()/1e6
            s.time_series[1].push(t, value * (2.5/(2**24-1)))
            time.sleep(sampling_dt)

        # Now synthesize the entire series.
        t, v = s.time_series[1].series
