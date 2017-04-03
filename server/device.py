import threading
import time
import logging
import numpy as np
import serial
from serial_lib import *
import re


class BioBoard(threading.Thread):
    '''Provides a direct connection to the biomonitor Serial port.
    ----- 
        Connect to a biomonitor device on a separate thread. Once started, an
        instance will search for a valid biomonitor device. When connected, it
        read data from the serial port. If a stream is started, and a suitable
        stream object is provided, data will stream to that object (could be an
        in-memory array, a Mongo database, etc.). 

        Pains have been taken to ensure the connection fails gracefully, but
        YMMV.
    '''

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
        # We'll run in a separate thread.
        threading.Thread.__init__(self)

        # Connect to the device.
        logging.basicConfig(level=verbose)
        self.log = logging.getLogger(__name__)
        self.info = self.log.info

        # Some variables for handling bad connection detection.
        self._bad_data_count = 0
        self._last_read_bad = False

        # Status variables.
        self._is_connected = False
        self.go = True
        self.do_stream = False
        self._trouble = False

        # Connection variables.
        self.port = port
        self.baud_rate = baud_rate

        # Board communications & conversion stuff.
        self.COV_FACTOR = 2.5 / (2**24-1)
        self.bio_regex = r"(B1)\s*(\d*)\s*(\w{0,8})\s*(\w*)"


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
                    if (self.is_connected and self.go):
                        self.log.info(' > Reading data from biomonitor.')
                    while (self.is_connected and self.go):
                        self.collect(ser)

            # And we're leaving main run loop & the thread, honorably.
            self.info(' > Closing BioDriver. Bye!')
        except:
            # Something went sideways. But we'll still cleanly exit the thread.
            self.log.exception(' > BioBoard Critical Error! Closing down.')


    def kill(self):
        '''Kill this thread, with moderate prejudice.'''
        self.go = False
        self._is_connected = False


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
            try:
                output = ser.readline()
            except:
                log.exception(' > Serial connection failed unexpectedly.')
                output = ''
            parsed = re.search(self.bio_regex, str(output))
            return ((parsed) and (parsed.group(1) == 'B1')) # really legit?


    def collect(self, ser):
        '''Collect data from current serial connection.'''
        channel, timestamp, value = read_data(ser)

        # If no valid channel is present, increment bad_data_count.
        if channel and (self.do_stream) and (channel in self.stream.channels):
            # Valid data? Streaming? Listening to this channel? Okay then...
            ts = timestamp/1e6 + self.time_offset
            vl = value * self.COV_FACTOR
            self.stream.time_series[channel].push(ts, vl)

        if (channel is None):
            self.info(' > Hmm. Not seeing data at the moment...')
            self._trouble = True
            if self._last_read_bad:
                self._bad_data_count += 1
            self._last_read_bad = True
            if self._bad_data_count > 1:
                self._is_connected = False
                self._trouble = False
        else: 
            self._last_read_bad = False
            self._bad_data_count = 0
            self._trouble = False


    def stream_to(self, stream):
        '''Start saving data to specified filename via a time series object.'''

        # Specify a streamable object (like a session, for example).
        self.time_offset = time.time()
        self.stream = stream

        # Start the collection process.
        self.log.info(' > Starting to stream data to database.')
        self.do_stream = True


    def stop_stream(self):
        ''' Turn stream to database off.'''
        self.info(' > Stopping data collection.')
        self.do_stream = False


    @property
    def status_message(self):
        if self.do_stream:
            message = 'Biomonitor device streaming data.'
        elif self.is_connected:
            message = 'Biomonitor device connected.'
        elif self._trouble:
            message = 'Hmm. Not seeing data at the moment...'
        else:
            message = 'Searching for biomonitor device.'
        return message


    @property
    def is_active(self):
        '''Return Boolean indicating whether the thread is alive.'''
        return self.isAlive()


    @property
    def is_connected(self):
        '''Returns Boolean indicating whether we're talking to the board.'''
        return self._is_connected


if __name__ == '__main__':

    # Open a connection to the board. Try to start reading some data.
    board = BioBoard()
    board.start()
