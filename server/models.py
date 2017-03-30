from pymongo import MongoClient
from database import *
import logging as log


class ModelController(object):

    def __init__(self, model_name, database, data=None, _id=None,\
            verbose=log.INFO):

        # We have ourselves a database.
        self.db = database
        self.model_name = model_name
        self.collection = self.db[model_name]

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
            query = qwrap(_id)

    def read(self, _id):
        '''Find a specific model given its _id.'''
        self.model = self.collection.find_one(qry(_id))

    def list(self):
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
                self.log.exception(' > Critical error in creating session.')
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

    def update_model(self):
        '''Saves the current model to the database.'''
        self.collection.update_one(qry(self.model), {'$set': self.model})

    def read_model(self):
        '''Retrieve the model from the database.'''
        self.model = self.collection.find_one(qry(self._id))

    def delete_model(self):
        '''Delete the model from the database.'''
        self.collection.delete_one(qry(self._id))

    @property
    def required_attributes(self):
        return []


class SessionController(ModelController):
    '''Handle session creation, updating, and so on.'''

    def __init__(self, database, data=None, _id=None):
        ModelController.__init__(self, 'sessions', database, data=data,\
                _id=_id)

    def create(self, data):
        '''Create a new data session.'''
        self._create(data)

        # Add a time series for each channel in the session.
        for channel in self.model['channels']:
            # Create a new time series for each channel.
            channel['owner'] = self._id
            s = TimeSeriesController(self.db, data=channel)
            channel['time_series_id'] = s._id
        self.update_model()


class TimeSeriesController(ModelController):

    def __init__(self, database, data=None, _id=None):
        ModelController.__init__(self, 'time_series', database, data=data,\
                _id=_id)

    def create(self, data):
        data['segment_size'] = 2048
        data['frequency_cutoff_hz'] = 15
        self._create(data)

    @property
    def required_attributes(self):
        return ['owner', 'description', 'physical_channel']
    

if __name__=='__main__':

    client = MongoClient()
    database = client['biomonitor_dev']
    session = {'name':'Dialysis', 'channels': [{'physical_channel': 0,\
            'description': 'PVDF Sensor'}]}
    s = SessionController(database, data=session)
    

