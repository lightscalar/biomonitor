import sys
import numpy as np
import signal
import logging
from gevent.wsgi import WSGIServer
from database import *
from device import *
from flask import Flask, request
from flask_cors import *
from flask_restful import abort, Api, Resource, reqparse
from time import sleep, time
from ipdb import set_trace as debug


# Configure logging.
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# Create a RESTFUL web server.
app = Flask(__name__)
api = Api(app)
valid_headers = ['Content-Type', 'Access-Control-Allow-Origin', '*']
cors = CORS(app, allow_headers=valid_headers)
        
# Connect to the Mongo database.
db = connect_to_database() 

# Connect to a biomonitor.
board = BioBoard()
board.start()

# Ensure board is stopped when server is stopped.
def exit_gracefully(signal, frame):
    '''When we kill the server (via CTL-C), gracefully close board 
       connections as well.
    '''
    log.info(" > Closing down biomonitor board.")
    board.kill()
    sys.exit(0)


# Listen for a kill signal. Close down biomonitor connection.
signal.signal(signal.SIGINT, exit_gracefully)


class Status(Resource):
    '''Return the board connection status.'''
    def get(self):
        # Look at the board. Report its current status.
        data = {}
        data['isConnected'] = board.is_connected 
        data['statusMessage'] = board.status_message 
        return serialize_mongo(data)

    def post(self):
        model = request.json


class Sessions(Resource):
    '''Handles session creation and listing.'''

    def post(self):
        '''Create a new session model.'''

        # Grab data from request.
        session_data = request.json

        # Add a place for the data to live.
        for channel in session_data['channels']:
            channel['physical_channel'] =  
            phys_chan = channel['physical_channel']
            session_data['data'][phys_chan] = data_dict

        # Save to the Mongo Database!
        current_session = db.sessions.insert_one(session_data)
        return serialize_mongo(find_document(current_session.inserted_id, \
                db.sessions))

class Session(Resource):
    '''A data recording session resource.'''

    def get(self, session_id):
        '''Get an existing session model.'''
        session_data = find_document(session_id, db.sessions)
        return serialize_mongo(session_data)
        

'''Define our API routes.'''
# Obtain device status.
api.add_resource(Status, '/status', methods=['GET', 'POST'])

# Session creation and listing.
api.add_resource(Sessions, '/sessions', methods=['GET', 'POST'])

# Read session, edit session, etc.
allowed_methods = ['GET', 'POST', 'DELETE']
api.add_resource(Session, '/session/<session_id>', methods=allowed_methods)

# Command session (deprecated now, I think?)
api.add_resource(Command, '/command', methods=['POST'])


if __name__ =='__main__':

    # Launch a webserver.
    use_production = True

    if use_production:
        # More suitable for production.
        http_server = WSGIServer(('', 1492), app)
        http_server.serve_forever()
    else:
        # For debugging purposes.
        app.run(port=1492, debug=True, threaded=True)

