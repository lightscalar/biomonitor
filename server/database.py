'''Routines for dealing with MongoDB output.'''
import numpy as np
from bson import ObjectId
import numpy as np
import time
from pymongo import MongoClient
import logging
from ipdb import set_trace as debug


class DatabaseEngine(object):
    '''Provides API for handling all communication with the Mongo database.'''

    def __init__(self, db_name='biomonitor_dev', verbose=logging.INFO):

        # Set up logging.
        logging.basicConfig(level=verbose)
        self.log = logging.getLogger(__name__)

        try: # to connect to the database
            client = MongoClient()
            self.db = client[db_name]
            self.log.info(' > Connected to MongoDB.')
        except: # you cannot, for some reason, so...
            self.log.exception(' > Problem connecting to the database.')

    def create_session(self, session_data):
        '''Creates a new data recording session.
        INPUTS
            session_data - dict
                The data specified in the recording session. Contains the 
                following fields:
                    name - str
                        The name of the data session.
                    channels - list
                        A list of channels to record on, e.g.:
                            [{channelDescription: 'PPG Sensor',
                              physicalChannel: 0},
                             {channelDescription: 'PVFD Sensor',
                              physicalChannel: 1}]
        '''
        # Store session creation time (UNIX epoch).
        session_data['created_at'] = created_at() 

        # Attempt session creation.
        self.log.info(' > Attempting session creation. ')
        try:
            insertion = self.db.sessions.insert_one(session_data)
            self.log.info(' > Session creation successful.')
        except:
            insertion = None
            self.log.exception(' > Critical error in creating new session.')
    
        # Find the created session.
        session = find_inserted_document(insertion, self.db.sessions)

        # Return inserted document.
        return session

    def insert_segment(self, session, segment):
        '''Create a new segment containing accumulated measurements.'''

        # Create a new segment.
        new_segment = {}
        new_segment['created_at'] = created_at() 
        new_segment['owner'] = q(session)
        new_segment['data'] = segment.buffer
        new_segment['min_time'] = segment.min_time
        new_segment['max_time'] = segment.max_time
        new_segment['duration'] = segment.max_time - segment.min_time

        # Create a new segment.
        ack = self.db.segments.insert_one(new_segment)
        return ack

    def find_segments(self, session, min_time=0, max_time=np.inf):
        '''Find all segments from given session in specified time range.'''
        return list(self.db.segments.find({'owner': q(session)}))


class Segment(object):

    def __init__(self, channels=[0,1], maxsize=2048):

        self.channels = channels
        self.maxsize = maxsize
        self.buffer = {}
        self.itr = {}
        self.init_buffer()

    def init_buffer(self):
        self.min_time = np.inf
        self.max_time = 0
        for chn in self.channels:
            schn = str(chn)
            self.buffer[schn] = self.empty()
            self.itr[schn] = 0

    def empty(self):
        '''Reset to zeros.'''
        return {'time': list(np.zeros(self.maxsize)),
                'vals': list(np.zeros(self.maxsize))}

    @property
    def is_full(self):
        return (np.max([i for k, i in self.itr.items()]) > self.maxsize)

    def push(self, channel, timestamp, value):
        '''Push an observation into the segment.'''
        # Only add data to requested channels.
        if channel not in self.channels: return

        # Set max/min times.
        if timestamp < self.min_time:
            self.min_time = timestamp
        self.max_time = timestamp

        # Find pointer to current array element.
        chn = str(channel)
        itr = self.itr[chn]
        self.itr[chn] += 1
        
        # Add data to the buffer, if we're not full.
        if not self.is_full:
            self.buffer[chn]['time'][itr] = unix_time_in_microseconds()/1e6
            self.buffer[chn]['vals'][itr] = value

''' 
------------------------------------------------------------
Here are some helpful utility functions.
------------------------------------------------------------
'''
def created_at():
    '''Return a nice date/time string.'''
    return time.strftime('%Y-%m-%d@%H:%M:%S', time.localtime())


def unix_time_in_microseconds():
    '''Return current POSIX epoch in microseconds, as a 64-bit integer.'''
    return np.int64(time.time() * 1e6)


def q(record):
    return record['_id']


def qry(record):
    '''Return a query object for the specified record.'''
    return {'_id': q(record)}


def qwrap(_id):
    '''Wrap an _id object in a query dict.'''
    return {'_id': _id}


def get_latest(record, collection):
    '''Get the latest version of the record.'''
    return collection.find_one(qry(record))


def find_unique_resource(collection):
    '''Returns the single object present in the collection.'''
    the_object = collection.find_one()


def update_document(document, collection):
    '''Update the given document in the collection.'''
    query = {'_id': document['_id']}
    collection.update_one(query, {'$set': document}, upsert=False)


def find_document(document_id, collection):
    ''' Find a document in a collection given a document_id.'''
    query = {'_id': string_to_obj(document_id)}
    return collection.find_one(query)


def find_inserted_document(insertion_response, collection):
    '''Grab the recently inserted document (now with _id, etc.)'''
    if (insertion_response) and (insertion_response.acknowledged):
        doc = collection.find_one({'_id': insertion_response.inserted_id})
    else:
        doc = None
    return doc


def string_to_obj(string):
    return ObjectId(string)


def goodify(obj):
    '''Loop through a mongo object and convert '_id' field to string.'''
    if '_id' in obj:
        obj['_id'] = str(obj['_id'])
    return obj


def serialize_mongo(result):

    # If it is a list, iterate over it.
    if type(result) == list:
        out = []
        for obj in result:
            out.append(goodify(obj))
        return out
    else:
        out = goodify(result)
    return out


if __name__ == '__main__':

    # Create a database engine instance.
    dbase = DatabaseEngine()

    # Create a mock session.
    session = {'name': 'MJL.001', \
            'channels':[{'channelDescription': 'PVDF', 'physicalChannel': 0 }]}

    # Save the session.
    sess_out = dbase.create_session(session)

    segment = Segment([0])
    N = 4
    itr = 0
    while itr<N:
        print('> Collecting data.')
        while not segment.is_full:
            # We're collecting data!
            segment.push(0, time.time(), np.random.randint(2**24-1) )
        dbase.insert_segment(sess_out, segment)
        segment.init_buffer()
        itr+=1


