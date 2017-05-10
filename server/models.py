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
        if self.model:
            self.load_series()
            self.load_annotations()


    def load_annotations(self):
        '''Load all annotations.'''
        query = {}
        query['owner_id'] = self._id
        self.annotations = list(self.db.annotations.find(query))
        self.model['annotations'] = self.annotations


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
        self.mean_sampling_rate() # cache current sampling rates, etc.


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
                {'vals': 1, 'filtered':1, 'time':1}).\
                               sort('min_time', 1)
        # Concatenate segments.
        for seg in cursor:
            # v += seg['filtered']
            v += seg['filtered']
            t += seg['time']
        return (t, v)


    def in_range(self, min_time=0, max_time=np.inf):
        '''Return series in specified range.'''
        t,v = [],[]
        segments = self.db.segments
        query = {}
        query['owner_id'] = self._id
        query['is_flushed'] = True
        query['min_time'] = {'$gt': min_time}
        query['max_time'] = {'$lt': max_time}
        cursor = segments.find_one(query)
        for seg in cursor:
            v += seg['filtered']
            t += seg['time']
        return (t,v)


    def at_least(self, min_time):
        '''Return first segment with time greater than specified time.'''
        t,v = [], []
        segments = self.db.segments
        query = {}
        query['owner_id'] = self._id
        query['is_flushed'] = True
        query['min_time'] = {'$gte': min_time}
        segs = segments.find(query)
        print(segs.count())
        nb_segs = np.min([segs.count(), 3])
        # Grab the latest three segments; can fill the buffer that way.
        for k in range(nb_segs):
            seg = segs.next()
            v += seg['filtered']
            t += seg['time']
        return t,v


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
            # v += seg['vals']
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
        data['freq_cutoff'] = 10
        data['filter_order'] = 3
        data['filter_coefs'] = []
        data['start_time'] = -1
        self._create(data)
        self.add_segment()


    def add_segment(self, current_segment=None):
        '''Add a new segment to the time series.'''
        segment_data = {}
        segment_data['owner_id'] = self._id
        segment_data['segment_size'] = self.model['segment_size']
        if self.number_of_segments == 0:
            segment_data['initial_segment'] = True
        else:
            segment_data['initial_segment'] = False
        segment = SegmentController(self.db, data=segment_data)
        self._update()
        self.load_segment()


    @property
    def required_attributes(self):
        '''We need these guys to do anything useful.'''
        return ['owner_id', 'description', 'physical_channel']


    def calculate_reference_time(self, timestamp):
        '''Calculate the delta time reference such that we have time continuity
           with previous segment blocks. This allows users to pause the 
           collection and resume later without having huge time gaps. We still
           retain the actual time in the form of the unix epoch time.i
        '''
        dt, fs = self.mean_sampling_rate()
        seg = self.last_segment()

        # Reference time is such that current timestamp is sampled to match
        # the last segment.
        return (timestamp - (np.max(seg[0]) + dt))


    def push(self, timestamp, value):
        '''Push a new (timestamp, value) into the time series.'''

        # Check to see if there is room in the current segment.
        if self.segment.is_full:
            # Need to flush this segment to disk and start anew.
            self.filter_segment() # butterworth filter this guy.
            self.segment.flush()
            self.add_segment() 

        # If this is the first segment, reference time is current epoch time.
        if not self.segment.has_reference_time:
            if self.segment.is_initial_segment:
                self.segment.model['reference_time'] = timestamp
            else: # look at the last segment to get reference time.
                self.segment.model['reference_time'] = \
                        self.calculate_reference_time(timestamp)

        # Correct for start time offset.
        shifted_time = (timestamp - self.segment.model['reference_time'])

        # Check for expired segment (this timestamp too big to fit given the
        # average dt.
        if self.segment.is_expired(shifted_time, self.mean_dt):
            self.filter_segment() # butterworth filter this guy.
            self.segment.flush()
            self.add_segment() 
            self.segment.model['reference_time'] = \
                    self.calculate_reference_time(timestamp)
            # Recalculate the shift w.r.t new data.
            shifted_time = (timestamp - self.segment.model['reference_time'])

        # Otherwise keep stuffing data in there.
        self.segment.push(shifted_time, value, epoch=timestamp)


    def filter_segment(self):
        '''Run a low pass filter on the data in the current segment.'''

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

        # Filtering the data.
        self.segment.model['filtered'] = y_filt
        
        # Fast updates of time series and the segment.
        self.db.time_series.update_one(qwrap(self._id),\
                {'$set':{'filter_coefs': coefs}})
        self.db.segments.update_one(qwrap(self.segment._id),\
                {'$set':{'filtered': y_filt}})


    @property
    def props(self):
        '''Return the total duration and mean sampling rate of time series.'''

        # Do it all in a single query, rather than separate properties.
        query = {'owner_id': self._id}
        limit = {'min_time': 1, 'max_time': 1}
        segments = list(self.db.segments.find(query, limit))
        duration = np.sum([s['max_time'] - s['min_time'] for s in segments]) 
        samples = len(segments) * self.model['segment_size']
        sampling_rate = samples/duration
        if not duration:
            duration = 0
            sampling_rate = 0
        return duration, sampling_rate


    def mean_sampling_rate(self):
        '''Return the mean sampling rate of the entire series.'''
        query = {}
        query['owner_id'] = self._id
        query['is_flushed'] = True
        segments = self.db.segments.find(query) 
         
        # Estimate sampling rate in segments.
        dt = []
        for k, segment in enumerate(segments):
            dt.append(np.mean(np.diff(segment['time'])))

        # Cache the values.
        self.mean_dt = np.median(dt) if len(dt) > 0 else 0
        self.mean_fs = np.median(1/np.array(dt)) if len(dt) > 0 else 0
        return self.mean_dt, self.mean_fs 


    @property
    def number_of_segments(self):
        query = {}
        query['owner_id'] = self._id
        return self.db.segments.find(query).count()


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
        data['reference_time'] = -1

        # Time is incremental 'delta' time; unix epoch stores actual time.
        data['time'] = list(np.zeros(data['segment_size']))
        data['epoch'] = list(np.zeros(data['segment_size']))

        # vals stores raw values; filtered stores digitally filtered version.
        data['vals'] = list(np.zeros(data['segment_size']))
        data['filtered'] = list(np.zeros(data['segment_size']))

        # When the segment is full it is flushed to the database.
        data['is_flushed'] = False
        if '_id' in data: del data['_id']
        return data


    @property
    def is_full(self):
        '''Are the time/value buffers at capacity?'''
        return (self.model['itr'] > self.model['segment_size'])


    def flush(self):
        '''Flush current segment to the disk. Load new segment into object.'''

        # Officially publish the segment to the database..
        self.model['is_flushed'] = True
        
        # Update min/max times as well as segment duration.
        self.model['min_time'] = self.min_time
        self.model['max_time'] = self.max_time
        self.model['duration'] = self.duration

        # Push to database.
        self._update()


    def push(self, timestamp, value, epoch=None):
        '''Push an observation into the segment.'''

        # Increment pointer.
        itr = self.model['itr']
        self.model['itr'] += 1

        # Insert element at appropriate place!
        if not self.is_full:
            self.model['time'][itr] = timestamp
            self.model['vals'][itr] = value
            if epoch:
                self.model['epoch'] = epoch


    def is_expired(self, shifted_timestamp, dt):
        '''Is this segment expired with respect to given timestamp and dt?'''

        # If we wait too long to push a sample, reset reference time.
        safety_factor = 25
        we_know_dt = (dt>0)
        data_present = self.model['itr'] > 0
        big_jump = (shifted_timestamp - self.max_time) > (dt * safety_factor)
        expired = (we_know_dt * data_present * big_jump)
        if expired:
            itr = self.model['itr']
            self.model['time'] = self.model['time'][:itr]
            self.model['vals'] = self.model['vals'][:itr]
            self.model['filtered'] = self.model['filtered'][:itr]
        return expired


    @property
    def vals(self):
        '''The values recorded in this segment.'''
        return self.model['vals']


    @property
    def time(self):
        '''The time values recorded in this segment.'''
        return self.model['time']


    @property
    def min_time(self):
        '''Minimum time present in the segment.'''
        return np.min(self.model['time'])


    @property
    def max_time(self):
        '''Maximum time associated with segment.'''
        return np.max(self.model['time'])


    @property
    def duration(self):
        '''Total duration of the data in the segment.'''
        return (self.model['max_time'] - self.model['min_time'])

    
    @property
    def is_initial_segment(self):
        '''Are we the initial segment in this time series?'''
        return self.model['initial_segment']


    @property
    def has_reference_time(self):
        '''Have we specified the reference time?'''
        return self.model['reference_time'] > 0


if __name__=='__main__':

    '''Simulate connection to a data source.'''
    database = connect_to_database()

    if True: 
        session = {'name':'Randomness', 'channels': [{'physical_channel': 1,\
                'description': 'PVDF Sensor'}]}
        s = SessionController(database, data=session)
        ts = s.time_series[1]

        # Simulate a data collection.
        duration = 25
        sampling_rate = 500 # Hz
        sampling_dt = 1/sampling_rate
        start = time.time()
        while (time.time() - start) < duration:
            value = np.random.randint(2**24-1)
            t = unix_time_in_microseconds()/1e6
            s.time_series[1].push(t, value * (2.5/(2**24-1)))
            time.sleep(sampling_dt)

        # Wait for a while. Ensure there is continuity.
        time.sleep(4)

        start = time.time()
        while (time.time() - start) < duration:
            value = np.random.randint(2**24-1)
            t = unix_time_in_microseconds()/1e6
            s.time_series[1].push(t, value * (2.5/(2**24-1)))
            time.sleep(sampling_dt)

        # Now synthesize the entire series.
        t, v = s.time_series[1].series
