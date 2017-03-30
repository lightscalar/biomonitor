from database import *


if __name__ == '__main__':

    # Create a database engine instance.
    dbase = DatabaseEngine()

    # Create a mock session.
    session = {'name': 'MJL.001', \
            'channels':[{'channelDescription': 'PVDF', 'physicalChannel': 0 }]}

    # Save the session.
    sess_out = dbase.create_session(session)
    point = (0,1324,-242334) 
    dbase.insert_measurement(sess_out, point)
