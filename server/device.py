import threading
from time import sleep, time
import logging
import numpy as np
import serial
from serial_lib import *
import re


class BioBoard(threading.Thread):
    '''Direct connection to the Biomonitor Serial port.'''
    BIOMONITOR_REGEX = r"(B1)\s*(\d*)\s*(\w{0,8})\s*(\w*)"

    def __init__(self, port=None, baud_rate=921600, verbose=logging.INFO):
        '''Create a new thread that will communicate with the biomonitor.
        INPUTS
            port - string
                Name of port to connect to. If no port is specified we'll look
                for available USB ports and check them.
            baud_rate - int
                The serial port's expected baud rate.
            verbose - int
                Set the logging level of the connection. Default is INFO.
        '''
        # Connect to the device.
        logging.basicConfig(level=verbose)
        self.log = logging.getLogger(__name__)
        self.info = self.log.info
        threading.Thread.__init__(self)
        self._is_connected = False
        self.port = port
        self.baud_rate = baud_rate
        self.go = True
        self.do_stream = False
        self.COV_FACTOR = 2.5 / (2**24-1)

    def run(self):
        '''This is the main loop of the thread.'''
        self.log.info(' > Looking for biomonitor.') 
        try:
            while self.go: # main loop
                
                # Attempt to connect to the biomonitor!
                while (not self.is_connected) and (self.go):
                    self.connect()

                # We're connected, so open that serial port up!
                with serial.Serial(self.port, self.baud_rate, timeout=2) as\
                        ser:
                    self.info(' > Starting data collection.')
                    while (self.is_connected and self.go):
                        self.collect(ser)

            # And we're leaving main run loop & the thread, honorably.
            self.info(' > Closing BioDriver. Bye!')
        except:
            # Something went sideways. But we'll cleanly exit the thread.
            self.log.exception(' > BioDriver Critical Error! Closing down.')

    def kill(self):
        '''Kill this thread, with moderate prejudice.'''
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
        with serial.Serial(port, self.baud_rate, timeout=1) as ser:
            output = ser.readline()
            parsed = re.search(BIOMONITOR_REGEX, str(output))
            return ((parsed) and (parsed.group(1) == 'B1'))

    @property
    def is_active(self):
        return self.isAlive()

    @property
    def is_connected(self):
        return self._is_connected

    def collect(self, ser):
        '''Collect data from current serial connection.'''
        channel, timestamp, value = read_data(ser)
        if self.do_stream and (channel in self.stream.channels):
            ts = timestamp/1e6 + self.time_offset
            vl = value * self.COV_FACTOR
            self.stream.time_series[channel].push(ts, vl)

    def stream_to(self, stream):
        '''Start saving data to specified filename via a time series object.'''

        # Specify a streamable object (like a session, for example).
        self.time_offset = time()
        self.stream = stream

        # Start the collection process.
        self.log.info(' > Starting to stream data to database.')
        self.do_stream = True

    def stop_stream(self):
        ''' Turn stream to database off.'''
        self.info(' > Stopping data collection.')
        self.do_stream = False
