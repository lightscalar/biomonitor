from database import *
from pymongo import MongoClient()
import logging

DATABASE = 'biomonitor_dev'


class DataSession(object):
    '''A data session object. Coordinates creation of time series, etc.'''

    def __init__(self, session, verbo):

        # Set up logging.
        logging.basicConfig(level=verbose)
        self.log = logging.getLogger(__name__)

        # Define the segment size.
        self.SEGMENT_SIZE = 4096 # about 10 seconds @400Hz.

        try: # to connect to the database
            client = MongoClient()
            self.db = client[db_name]
            self.log.info(' > Connected to MongoDB.')
        except: # you cannot, for some reason, so...
            self.log.exception(' > Problem connecting to the database.')


        if '_id' in session: # session exists already.
            session = 


