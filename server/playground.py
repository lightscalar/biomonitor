from analysis import *


if __name__ == '__main__':

    db = connect_to_database()
    sess_1 = 'MJL.N02'
    s1 = grab_session(session_name=sess_1)
    segment_size = s1.time_series[1].model['segment_size']


