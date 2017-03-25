import numpy as np
import logging
from serial_lib import *
import serial 
import threading
from time import sleep, time
import re
from ipdb import set_trace as debug


# Set the log level for the device connections, etc.
LOG_LEVEL = logging.INFO 
 

class BioDriver(threading.Thread):
    '''Direct connection to the Biomonitor Serial port.'''
    BIOMONITOR_REGEX = r"(B1)\s*(\d*)\s*(\w{0,8})\s*(\w*)"

    def __init__(self, port=None, baud_rate=921600):
        '''Create a new thread that will communicate with the biomonitor.
        INPUTS
            port - string
                Name of port to connect to. If no port is specified we'll look
                for available USB ports and check them.
            baud_rate - int
                The serial port's expected baud rate.
        '''
        # Connect to the device.
        logging.basicConfig(level=LOG_LEVEL)
        self.logger = logging.getLogger(__name__)
        self.info = self.logger.info
        threading.Thread.__init__(self)
        self._is_connected = False
        self.port = port
        self.baud_rate = baud_rate
        self.go = True
        self.start_time = time() 

    def run(self):
        '''This is the main loop of the thread.'''
        self.logger.info(' > Looking for biomonitor.') 
        try:
            while self.go: # main loop
                # Attempt to connect to the biomonitor!
                while (not self.is_connected):
                    self.connect()

                # We're connected, so open that serial port up!
                with serial.Serial(self.port, self.baud_rate, timeout=2) as\
                        ser:
                    self.info(' > Starting data collection.')
                    while (self.is_connected and self.go):
                        self.collect(ser)

            # And we're leaving min run loop & the thread, honorably.
            self.info(' > Closing BioDriver. Bye!')
        except:
            # Something went sideways. But we'll exit the thread.
            self.logger.exception(' > A problem occurred in\
                    the BioDriver! Closing down.')

    def kill(self):
        '''Kill this thread. With moderate prejudice.'''
        self.go = False

    def connect(self):
        '''Attempt to connect to the serial monitor.'''
        ports = find_serial_devices()
        for port in ports:
            self.info(' > Pinging {:s}'.format(port))
            if self.ping(port):
                self.info(' > Connected to biomonitor on {:s}.'.format(port))
                self.port = port
                self._is_connected = True
                return

    def ping(self, port):
        '''Ping the serial port. See if a legit biomonitor lives there.'''
        # for attempts in range(10):
        with serial.Serial(port, self.baud_rate, timeout=1) as ser:
            output = ser.readline()
            parsed = re.search(BIOMONITOR_REGEX, str(output))
            return ((parsed) and (parsed.group(1) == 'B1'))

    @property
    def is_alive(self):
        return self.isAlive()

    @property
    def is_connected(self):
        return self._is_connected

    def collect(self, ser):
        '''Collect data from current serial connection.'''
        # (c, t, v) = read_data(ser)
        self.data = read_data(ser)


def status_message():
    message = {}
    message['isConnected'] = False
    message['statusMessage'] = 'Nothing to report'
    message['availableDevices'] = []
    return message


def check_device_connection(status_collection):
    '''Connect to the biomonitor, if present. Update the library's status.
    INPUTS
        status_collection - object
            The status collection of the Mongo database.
    '''
    # Clear out any existing status messages.
    status_collection.delete_many({})
    status_dict = status_message()

    # Verify that something is on the port.
    available_devices = find_serial_devices()
    status_dict['availableDevices'] = available_devices
    if len(available_devices) == 0:
        status_dict['isConnected'] = False
        status_dict['statusMessage'] = 'Nothing connected to USB port!'
    else:
        status_dict['isConnected'] = True
        if len(available_devices)>1:
            status_dict['statusMessage'] = '{:d} devices available on USB.'\
                    .format(len(available_devices))
        else:
            status_dict['statusMessage'] = 'One device available on USB.'

    # Update the MongoDB.
    status_collection.insert_one(status_dict)

    # Return for convenience.
    return status_dict


if __name__=='__main__':
    # from pymongo import MongoClient

    # # Connect to the MongoDB!
    # client = MongoClient()
    # db = client['biomonitor_dev']
    # status = db.status

    # # Let's check the connection.
    # out = check_device_connection(status) 
    
    d = BioDriver()
    d.start()

    
    
        
    
