from glob import glob
import re


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
