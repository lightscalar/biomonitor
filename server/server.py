import sys
import numpy as np
import signal
import logging
from gevent.wsgi import WSGIServer
from database import *
from models import *
from device import *
from flask import Flask, request, abort
from flask_cors import *
from flask_restful import abort, Api, Resource, reqparse
from time import sleep, time
from ipdb import set_trace as debug
from analysis import *
from sig_proc import *
from bson import ObjectId
from processor import *


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
        data['is_connected'] = board.is_connected 
        data['status_message'] = board.status_message 
        data['device_port'] = board.port 
        return serialize(data)


class Sessions(Resource):
    '''Handles session creation and listing.'''

    def get(self):
        '''List all sessions in the databse.'''
        data = SessionController(db) # will list if no _id provided.
        return serialize(data.models)

    def post(self):
        '''Create a new session model.'''
        # Grab data from request.
        data = request.json
        data = deserialize(data)
        session = SessionController(db, data=data)
        return serialize(session.model)


class Session(Resource):
    '''A data recording session resource.'''

    def get(self, session_id):
        '''Get an existing session model.'''
        session = SessionController(db, _id=session_id)
        return serialize(session.model)

    def delete(self, session_id):
        '''Delete current session, and its associated time series, etc.'''
        session = SessionController(db, _id=session_id)
        session.delete() # this will delete all child time series, etc.

    def put(self, session_id):
        '''Provides commands to start/stop recording data to a session.'''
        data = request.json
        data = deserialize(data)
        s = SessionController(db, _id=session_id)
        command = data['cmd']
        if command == 'start': # start streaming data to session
            board.stream_to(s)
        elif command=='stop':
            board.stop_stream()


class Annotations(Resource):

    def post(self):
        '''Create a new annotation.'''
        data = request.json
        data = deserialize(data)
        db.annotations.insert_one(data)


class Annotation(Resource):
    '''A data recording session resource.'''

    def delete(self, annotation_id):
        '''Delete specified annotation, and its associated time series, etc.'''
        db.annotations.delete_one({'_id': ObjectId(annotation_id)})


class DataHistory(Resource):
    '''Returns all available data for a given data session.'''

    def get(self, session_id):
        '''Return entire data series.'''
        s = SessionController(db, _id=session_id)
        if not s._id: abort(404)
        
        # Return all data on all available channels.
        series_data = []
        for channel, ts in s.time_series.items():
            time_series = ts.model
            t,v = ts.series
            time_series['data'] = list(zip(t,v))
            series_data.append(time_series)

        # Return all available data for this session.
        return serialize(series_data)


class StreamData(Resource):

    def get(self, session_id):
        '''Get whatever segment of time series is available.'''

        # Specify the frequency to display to web.
        target_frequency = 100

        # Extract query parameters (range on stream request).
        min_time = request.args.get('min')
        max_time = request.args.get('max')

        # Make sure range is valid.
        min_time = float(min_time) if min_time else 0
        max_time = float(max_time) if max_time else np.inf

        if min_time < 0:
            min_time = 0
        # if max_time < 0:
        #     max_time = np.inf

        s = SessionController(db, _id=session_id)
        series_data = []
        # print('Minimum time is: {:.2f}'.format(min_time))
        # print('Maximum time is: {:.2f}'.format(max_time))
        for channel, series in s.time_series.items():
            time_series = series.model

            # Actual data.
            if max_time<0:
                t,v = series.last_segment()
            else:
                try:
                    # print('Getting at least...')
                    t,v = series.at_least(min_time)
                except:
                    t,v = [],[]

            if len(t)>0:
                # Downsample data for display purposes.
                t_,v_ = downsample(t, v, target_frequency)

                # For demonstration purposes, compute quanities of interest.
                # This is super inefficient! Don't do this in general. Cache!
                t_all, v_all = series.series
                t_all = np.array(t_all)
                v_all = np.array(v_all)
                t_cur = np.mean(t)
                delta_t = 20
                idx = dex((t_all>t_cur-delta_t)*(t_all<t_cur+delta_t))
                bpm = estimate_bpm(t_all[idx], v_all[idx])
                # print('LEN: {:d}'.format( len(t_all)))
                # print('t: {:f}'.format( t_cur))
                _, _, _, metric = golden_representation(t_all[idx],\
                        v_all[idx])
            else:
                t_cur = -1
                bpm = 0
                metric = 0
                t_, v_ = t,v
                
            # Add data, sampling rate, current time, beats per minute, etc.
            time_series['data'] = list(zip(t_,v_))
            time_series['bpm'] = bpm
            time_series['metric'] = metric
            time_series['duration'], time_series['sampling_rate'] = \
                    series.props
            if len(t)>0:
                time_series['min_time'] = np.min(t)
                time_series['max_time'] = np.max(t)
                # print(time_series['max_time'])
            else: # All out of data.
                time_series['min_time'] = -1
                time_series['max_time'] = -1

            # Add current time series to the series list.
            series_data.append(time_series)

        # Aaaand we're done.
        return serialize(series_data)
        

'''Define our API routes.'''
# Obtain device status.
api.add_resource(Status, '/status', methods=['GET', 'POST'])

# Session creation and listing.
api.add_resource(Sessions, '/sessions', methods=['GET', 'POST'])

# Read session, edit session, etc.
allowed_methods = ['GET', 'PUT', 'DELETE']
api.add_resource(Session, '/session/<session_id>', methods=allowed_methods)

# Stream time series data.
path = '/session/<session_id>/stream'
api.add_resource(StreamData, path, methods=['GET'])

# Expose all available historical data for this stream.
path = '/session/<session_id>/history'
api.add_resource(DataHistory, path, methods=['GET'])

# Add annotations.
path = '/annotations'
api.add_resource(Annotations, path, methods=['GET', 'POST'])

# Add annotation.
path = '/annotation/<annotation_id>'
api.add_resource(Annotation, path, methods=['DELETE'])

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

