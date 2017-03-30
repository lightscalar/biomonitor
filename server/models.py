from pymongo import MongoClient
from database import *
import logging as log
from ipdb import set_trace as debug


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

        assert (data is not None) or (_id is not None),\
            'Must supply session data or _id.'

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
        return list(self.collection.find())

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
        ModelController.__init__(self, 'sessions', database, data=data,\
                _id=_id)

    def read(self):
        '''Read a specific session from the database.'''
        self._read()
        self.sideload_time_series()

    def sideload_time_series(self):
        for chn in self.model['channels']:
            _id = chn['time_series_id']
            self.sideload['time_series'][chn['physical_channel']] =\
                    TimeSeriesController(self.db, _id=_id)

    def create(self, data):
        '''Create a new data session.'''
        self._create(data)

        # Add a time series for each channel in the session.
        self.sideload['time_series'] = {}
        for channel in self.model['channels']:
            # Create a new time series for each channel.
            channel['owner'] = self._id
            ts = TimeSeriesController(self.db, data=channel)
            channel['time_series_id'] = ts._id
        self._update()
        self.sideload_time_series()

    @property
    def time_series(self):
        return{k: self.sideload['time_series'][k] \
                for k in self.sideload['time_series'].keys()}

    @property
    def channels(self):
        '''Expose the channel keys.'''
        return self.time_series.keys()


class TimeSeriesController(ModelController):

    def __init__(self, database, data=None, _id=None):
        ModelController.__init__(self, 'time_series', database, data=data,\
                _id=_id)

    def read(self):
        '''Read the current time series from the database.'''
        self._read()
        self.sideload_segment()

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

    def sideload_segment(self):
        '''Load the latest segment.'''
        latest = self.db.segments.\
                find({'owner':self._id}, {'_id':1}).\
                sort([('created_at', -1)]).\
                limit(-1).next()
        self.segment = SegmentController(self.db, _id=q(latest))

    def create(self, data):
        # Create the time series object.
        data['segment_size'] = 1024
        data['frequency_cutoff_hz'] = 15
        self._create(data)
        self.add_segment()

    def add_segment(self, current_segment=None):
        '''Add a new segment to the data series.'''
        segment_data = {}
        segment_data['owner'] = self._id
        segment_data['segment_size'] = self.model['segment_size']
        segment_data['frequency_cutoff_hz'] = self.model['frequency_cutoff_hz']
        segment_data['filter_order'] = 5
        segment_data['current_filter_coef'] =\
                np.zeros(segment_data['filter_order']).tolist()
        segment = SegmentController(self.db, data=segment_data)
        self._update()
        self.sideload_segment()

    @property
    def required_attributes(self):
        '''We need these guys to do anything useful.'''
        return ['owner', 'description', 'physical_channel']

    def push(self, timestamp, value):
        '''Push a new value into the time series.'''

        if self.segment.is_full:
            # Need to flush this segment to disk and start anew.
            self.segment.flush()
            self.add_segment() # TODO: PROPAGATE FILTER COEFFICIENTS HERE.

        # Otherwise keep stuffing data in there.
        self.segment.push(timestamp, value)
    

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

    client = MongoClient()
    database = client['biomonitor_dev']
    session = {'name':'Dialysis', 'channels': [{'physical_channel': 1,\
            'description': 'PVDF Sensor'}]}
    s = SessionController(database, data=session)

    duration = 5
    sampling_rate = 500 # Hz
    sampling_dt = 1/sampling_rate
    start = time.time()
    while (time.time() - start) < duration:
        value = np.random.randint(2**24-1)
        t = unix_time_in_microseconds()/1e6
        s.time_series[1].push(t, value)
        time.sleep(sampling_dt)

    # Now synthesize the entire series.
    t, v = s.time_series[1].series
