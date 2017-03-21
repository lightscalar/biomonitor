import numpy as np
from glob import glob
import re


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


def status_message():
    message = {}
    message['isConnected'] = False
    message['statusMessage'] = 'Nothing to report'
    message['availableDevices'] = []
    return message


def check_connection(status_collection):
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
    from pymongo import MongoClient

    # Connect to the MongoDB!
    client = MongoClient()
    db = client['biomonitor_dev']
    status = db.status

    # Let's check the connection.
    out = check_connection(status) 

    
        
    
