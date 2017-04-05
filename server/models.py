from pymongo import MongoClient
from bson import ObjectId
from database import *
import logging as log
from ipdb import set_trace as debug
from filters import lowpass


class ModelController(object):
    '''Base class for dealing with models, saving to database, etc.
    ---
    This class provides basic CRUD functionality for a Mongo database. The
    idea is to extend this class to provide model-specific requirements.
    For example, we can side-load time series on a data session, update
    time series segments, etc.
    '''

    def __init__(self, model_name, database, data=None, _id=None,\
            verbose=log.INFO):
        '''Connect to database. Load or create the model.'''

        # We have ourselves a database.
        self.db = database
        self.model_name = model_name
        self.collection = self.db[model_name]

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
            if (type(_id) is str): # convert to ObjectId format
                _id = ObjectId(_id)
            self._id = _id
            self.read()


    def _read(self):
        '''Find a specific model given its _id.'''
        self.model = self.collection.find_one(qwrap(_id))


    def _list(self):
        '''Return a collection of all models in the database.'''
        self.models = list(self.collection.find())
        return self.models


    def _delete(self):
        '''Delete the current resource.'''
        self.collection.delete_one(qwrap(self._id))


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
        self.collection.delete_one(qwrap(self._id))

    @property
    def required_attributes(self):
        return []


class SessionController(ModelController):
    '''Handle session creation, updating, and so on.
    ----
        A session refers to a data recording session. A session generally 
        records data on multiple channels, which are represented by 
        time series.
    '''

    def __init__(self, database, data=None, _id=None):
        '''Initialize the model as a sessions object.'''
        ModelController.__init__(self, 'sessions', database, data=data,\
                _id=_id)


    def read(self):
        '''Read a specific session from the database.'''
        self._read()
        self.load_series()


    def delete(self):
        '''Delete current session and all associated time series.'''
        
        # First find all the time series I own; delete those.
        cursor = self.db.time_series.find({'owner_id': self._id})
        for ts in cursor:
            series = TimeSeriesController(self.db, _id=ts['_id'])
            series.delete() # will take care of its own segment deletion.

        # And now, I delete myself.
        self._delete()

    def load_series(self):
        '''Add channel TimeSeries objects to dictionary indexed by physical
           channel.'''
        # Loop over the declared channels.
        self._series = {}
        for channel in self.model['channels']:

            # What is the physical channel number?
            pchn = channel['physical_channel']
            query = {'owner_id': self._id, 'physical_channel': pchn}
            
            # Find time series corresponding to the channel.
            s_id = self.db.time_series.find_one(query, {'_id':1})
            self._series[pchn] = TimeSeriesController(self.db, _id=q(s_id))


    def create(self, data):
        '''Create a new data session.'''
        self._create(data)

        # Add a time series for each channel in the session.
        for channel in self.model['channels']:
            # Create a new time series for each channel.
            channel['owner_id'] = self._id
            ts = TimeSeriesController(self.db, data=channel)
        self.load_series()


    @property
    def time_series(self):
        '''Return the synthesized time series.'''
        return self._series


    @property
    def channels(self):
        '''Expose the channel keys.'''
        return self.time_series.keys()


class TimeSeriesController(ModelController):
    '''Model time series data. Handle segment creation, filtering, etc.
    -----
        A time series is, well, a series of timestamped data values. Because
        of the limitations of MongoDB document sizes (< 16 MB), a given 
        time series is actually split up into a sequence of non-overlapping,
        fixed-length segments. 
    '''

    def __init__(self, database, data=None, _id=None):
        '''Create or load the time series.'''
        ModelController.__init__(self, 'time_series', database, data=data,\
                _id=_id)


    def read(self):
        '''Read the current time series from the database.'''
        self._read()
        self.load_segment()


    def delete(self):
        '''Delete current time series, as well as all segments.'''

        # First, delete all the segments that I own.
        self.db.segments.delete_many({'owner_id': self._id})

        # Now delete myself! Au revoir, cruel world.
        self._delete()


    @property
    def series(self):
        '''Synthesize entire series from the available segments.'''
        # Initialize time and value lists.
        t,v = [],[]
        segments = self.db.segments
        cursor = segments.find({'owner_id':self._id, 'is_flushed':True},\
                               {'filtered':1, 'time':1}).\
                               sort('min_time', 1)
        # Concatenate segments.
        for seg in cursor:
            v += seg['filtered']
            t += seg['time']
        return (t, v)


    def series_range(self, min_time=0, max_time=np.inf):
        '''Return series in specified range.'''
        t,v = [],[]
        segments = self.db.segments
        query = {}
        query['owner_id'] = self._id
        query['is_flushed'] = True
        query['min_time'] = {'$gt': min_time}
        query['max_time'] = {'$lt': max_time}
        cursor = segments.find(query)
        for seg in cursor:
            v += seg['filtered']
            t += seg['time']
        return (t,v)


    def last_segment(self):
        '''Return just the latest relevant segment.'''
        t,v = [],[]
        segments = self.db.segments
        query = {}
        query['owner_id'] = self._id
        query['is_flushed'] = True
        try:
            seg = segments.find(query).sort('$natural',-1).next()
        except:
            seg = None
        if seg:
            v += seg['filtered']
            t += seg['time']
        return (t,v)


    def load_segment(self):
        '''Load the latest segment.'''
        latest = self.db.segments.\
                find({'owner_id':self._id}, {'_id':1}).\
                sort([('created_at', -1)]).\
                limit(-1).next()

        # Assign current segment as attribute on this time series.
        self.segment = SegmentController(self.db, _id=q(latest))


    def create(self, data):
        # Create the time series object.
        data['segment_size'] = 800
        data['freq_cutoff'] = 6
        data['filter_order'] = 5
        data['filter_coefs'] = []
        data['start_time'] = -1
        self._create(data)
        self.add_segment()


    def add_segment(self, current_segment=None):
        '''Add a new segment to the data series.'''
        segment_data = {}
        segment_data['owner_id'] = self._id
        segment_data['segment_size'] = self.model['segment_size']
        segment = SegmentController(self.db, data=segment_data)
        self._update()
        self.load_segment()


    @property
    def required_attributes(self):
        '''We need these guys to do anything useful.'''
        return ['owner_id', 'description', 'physical_channel']


    def push(self, timestamp, value):
        '''Push a new value into the time series.'''
        if self.model['start_time'] < 0: # First observation establishes start.
            self.model['start_time'] = timestamp
            self._update()

        # Correct for start time offset.
        timestamp -= self.model['start_time']

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


class SegmentController(ModelController):
    ''' A fixed-size document that holds the actual data in a time series.
    -----
        A fixed-length segment of a time series collection. Holds the actual
        data. It must be associated with a time series object. The time series
        object actually handles the creating, updating, and filtering, and the
        stitching together of individual segments.
    '''

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

    '''Simulate connection to a data source.'''
    database = connect_to_database()

    if True: 
        session = {'name':'Dialysis', 'channels': [{'physical_channel': 1,\
                'description': 'PVDF Sensor'}]}
        s = SessionController(database, data=session)

        # # Simulate a data collection.
        # duration = 5
        # sampling_rate = 500 # Hz
        # sampling_dt = 1/sampling_rate
        # start = time.time()
        # while (time.time() - start) < duration:
        #     value = np.random.randint(2**24-1)
        #     t = unix_time_in_microseconds()/1e6
        #     s.time_series[1].push(t, value * (2.5/(2**24-1)))
        #     time.sleep(sampling_dt)

        # # Now synthesize the entire series.
        # t, v = s.time_series[1].series
