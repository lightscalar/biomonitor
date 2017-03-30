from pymongo import MongoClient

if __name__=='__main__':

    client = MongoClient()
    db = client['biomonitor_dev']

    go_nogo = input(' > Wipe development database? (Y/n): ')
    if (go_nogo == 'Y'):
        db.sessions.delete_many({})
        db.time_series.delete_many({})
        db.segments.delete_many({})
    else:
        print(' > Chicken.')
