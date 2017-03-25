import numpy as np
import serial 
from ipdb import set_trace as debug
from time import time
from glob import glob
from database import *
import re


# Relevant Constants.
BIOMONITOR_REGEX = r"(B1)\s*(\d*)\s*(\w{0,8})\s*(\w*)"
MAXVAL = 2**24-1
MAXREF = 2.5
COVFAC = MAXREF*(1/MAXVAL)
ALLOWED_CHANNELS = [str(k) for k in [0,1,5]]
MAX_BUFFER_SIZE = 2000


def find_serial_devices():
    '''Find serial devices connected to the computer.'''
    
    # Define the REGEX for finding a serial port!
    SERIAL_REGEX = r"/dev/tty.usbserial"

    # Grab list of devices.
    devices = glob('/dev/*')
    valid_devices = []
    for device in devices: 
        if re.search(SERIAL_REGEX, device):
            valid_devices.append(device)
    return valid_devices


def read_data(ser):
    '''Read data from the biomonitor at serial connection ser.'''
    biomonitor_output = ser.readline()
    parsed = re.search(BIOMONITOR_REGEX, str(biomonitor_output))
    channel_number, timestamp, value = None, None, None
    if parsed:
        # We caught something!
        if parsed.group(1) == 'B1':
            # Looks like we have some BioMonitor output.
            try: # channel number there?
                channel_number = int(parsed.group(2), 16)
            except:
                pass
            try: # voltage value present?
                value = int(parsed.group(3),16)
            except:
                pass
            try: # timestamp present?
                timestamp = int(parsed.group(4),16)
            except:
                pass
    return (str(channel_number), timestamp, value)


def send_command(command_str, session_id, db):
    '''Send a command to start a collection in a given session.
    INPUTS
        command_str - string
            One of {COLLLECT, IDLE} that determines whether to collect data
            from the device, or remain idle.
        session_id - object
            The session ID for the session to which we should dump the data.
        db - object
            The MongoDB object.
    '''
    command = {}
    command['type'] = command_str
    command['params'] = {'session_id': session_id}
    db.command_buffer.insert_one(command)
    

class Biomonitor(object):

    def __init__(self, db, serial_port, baud_rate=921600):
        # Initialize stuff
        self.serial_port = serial_port
        self.baud_rate = baud_rate
        self.db = db
        self._command = {'type': 'IDLE'}
        self.itr_max = 500000
        self.value_buffer = {k:[] for k in ALLOWED_CHANNELS}
        self.timestamp_buffer = {k:[] for k in ALLOWED_CHANNELS}

        # Listen for command. Repeat.
        while True:
            self.do()

    def get_command(self):
        '''Grab command from the command buffer.'''
        command = db.command_buffer.find_one()
        if command:
            self._command = command
            db.command_buffer.delete_many({})
            self.process_command()

    def process_command(self):
        '''Extract useful parameters from the command.'''
        self._session = find_document(self._command['params']['session_id'],\
                db.sessions)
        self._channels = [chn['physicalChannel'] \
                for chn in self._session['channels']]

    def flush_data_buffer(self):
        '''Empty current data buffer to the Mongo database.'''
        # To what session are we flushing data?
        sess_id = self._session['_id']
        query = {'_id': sess_id}

        # Get values and timestamps
        values = self.value_buffer
        timestamps = self.timestamp_buffer

        # Loop through all channels.
        for channel_number in self._channels:
            t = timestamps[channel_number]
            v = values[channel_number]
            t_ = 'data.{:s}.timestamps'.format(channel_number)
            v_ = 'data.{:s}.values'.format(channel_number)
            self.db.sessions.update_one(query, {'$push': {t_: {'$each': t}}})
            self.db.sessions.update_one(query, {'$push': {v_: {'$each': v}}})

    def do(self):
        '''Do what you're told to do unless something changes.'''
        itr = 0

        start_time = time()
        with serial.Serial(self.serial_port, self.baud_rate, timeout=0) as ser:

            while (self._command['type'] == 'COLLECT'):

                # Grab data coming from the BIOMONITOR.
                channel_number, timestamp, value = read_data(ser)
                print(itr)

                if channel_number: # did we see any data on the serial port?
                    if channel_number in self._channels: # do we care?
                        self.value_buffer[channel_number].append(value)
                        self.timestamp_buffer[channel_number].append(timestamp)
                        if (len(self.value_buffer[channel_number]) >\
                                MAX_BUFFER_SIZE):
                            # Upload current data to the database.
                            self.flush_data_buffer()
                    
                # Update command every so often.
                if np.mod(itr, self.itr_max)==0:
                    debug()
                    print('> COLLECTION MODE')
                    self.get_command()
                    itr = 0
                itr += 1

            while (self._command['type'] == 'IDLE'):
                # Just hang out. Don't do anything stupid. But check for the
                # latest commands.
                if np.mod(itr, self.itr_max)==0:
                    print('> IDLE MODE')
                    self.get_command()
                    itr = 0
                itr += 1


if __name__=='__main__':
    from pymongo import MongoClient

    client = MongoClient()
    db = client['biomonitor_dev']
    sessions = list(db.sessions.find())
    session = sessions[-1]
    command_buffer = db.command_buffer

    devices = find_serial_devices()
    # b = Biomonitor(db, devices[0])


