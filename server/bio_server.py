import numpy as np
from pymongo import MongoClient
from flask import Flask, request
from flask_restful import abort, Api, Resource
from flask_restful import reqparse
from flask_cors import *
from time import sleep, time
from database import *

# Create a new web server.
app = Flask(__name__)
api = Api(app)
cors = CORS(app, allow_headers=["Content-Type",\
        "Access-Control-Allow-Origin", '*'])
client = MongoClient()
db = client['biomonitor_dev']


class Status(Resource):

    def get(self):
        status = find_unique_resource('status')

    def post(self):
        model = request.json


class Model(Resource):

    def get(self, model_id):
        # Get an existing model.
        return find_scan(model_id)


# Define our API routes.
api.add_resource(Models, '/models', methods=['GET', 'POST'])
api.add_resource(Model, '/model/<model_id>', methods=['GET', 'POST',\
        'DELETE'])


if __name__ =='__main__':

    # Launch the web server (not suitable for production!
    app.run(port=1492, debug=True, threaded=True)

