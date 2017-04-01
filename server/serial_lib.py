from glob import glob
import re
from ipdb import set_trace as debug
from bson import ObjectId


BIOMONITOR_REGEX = r"(B1)\s*(\d*)\s*(\w{0,8})\s*(\w*)"


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
                value = int(parsed.group(3), 16)
            except:
                pass
            try: # timestamp present?
                timestamp = int(parsed.group(4), 16)
            except:
                pass
    return (channel_number, timestamp, value)


def camel_to_snake(camel):
    '''Convert camelCase to snake_case.'''
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', camel)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def snake_to_camel(snake):
    '''Convert snake_case to camelCase.'''
    return re.sub(r'(?!^)_([a-zA-Z])', lambda m: m.group(1).upper(), snake)


def deserialize(obj, key=None):
    '''Return object if it is simple; otherwise recursively iterate through.'''
    if (type(obj) is list): # loop through elements
        nlist = []
        for el in obj:
            nlist.append(deserialize(el))
        return nlist
    elif (type(obj) is dict): # loop through key,value pairs
        ndict = {}
        for k,v in obj.items():
            ndict[camel_to_snake(k)] = deserialize(v, key=k)
        return ndict
    else: # convert string _id to ObjectId, etc.
        if (type(obj) is str) and (re.search(r'(_id)', key)):
            # Convert into an ObjectId.
            return ObjectId(obj)
        else:
            return obj


def serialize(obj, key=None):
    '''Return object if it is simple; otherwise recursively iterate through.'''
    if (type(obj) is list): # loop through elements
        nlist = []
        for el in obj:
            nlist.append(serialize(el))
        return nlist
    elif (type(obj) is dict): # loop through key,value pairs
        ndict = {}
        for k,v in obj.items():
            ndict[snake_to_camel(k)] = serialize(v, key=k)
        return ndict
    else: # convert string _id to ObjectId, etc.
        if (type(obj) is ObjectId) and (re.search(r'(_id)', key)):
            # Convert into an ObjectId.
            return str(obj)
        else:
            return obj
