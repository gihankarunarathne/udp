from curwmysqladapter import mysqladapter
import sys, traceback, csv, json, datetime, getopt, glob, os

def usage() :
    usageText = """
Usage: ./CSVTODAT.py [-d YYYY-MM-DD] [-h]

-h  --help          Show usage
-d  --date          Date in YYYY-MM-DD. Default is current date.
-t  --time          Time which need to run the forecast in HH:MM:SS format.
-f  --force         Force insert timeseries. If timeseries exists, delete existing data and replace with new data.
-r  --rainfall      Store rainfall specifically. Ignore others if not mentioned.
-e  --discharge     Store discharge(emission) specifically. Ignore others if not mentioned.
-w  --waterlevel    Store waterlevel specifically. Ignore others if not mentioned.
    --wl_out_suffix Suffix for 'water_level-<SUFFIX>' output directories. 
                    Default is 'water_level-<YYYY-MM-DD>' same as -d option value.
"""
    print(usageText)

try :
    CONFIG = json.loads(open('CONFIG.json').read())
    # print('Config :: ', CONFIG)

    DISCHARGE_NUM_METADATA_LINES = 2
    DISCHARGE_CSV_FILE = 'DailyDischarge.csv'
    RAIN_CSV_FILE = 'DailyRain.csv'
    WATER_LEVEL_DIR_NAME = 'water_level'
    RF_DIR_PATH = '/mnt/disks/wrf-mod/OUTPUT/'
    OUTPUT_DIR = './OUTPUT'
    RAIN_GUAGES = ['Attanagalla', 'Colombo', 'Daraniyagala', 'Glencourse', 'Hanwella', 'Holombuwa', 'Kitulgala', 'Norwood']
    DAY_INTERVAL = 24 # In hours

    MYSQL_HOST="localhost"
    MYSQL_USER="root"
    MYSQL_DB="curw"
    MYSQL_PASSWORD=""

    if 'DISCHARGE_CSV_FILE' in CONFIG :
        DISCHARGE_CSV_FILE = CONFIG['DISCHARGE_CSV_FILE']
    if 'RAIN_CSV_FILE' in CONFIG :
        RAIN_CSV_FILE = CONFIG['RAIN_CSV_FILE']
    if 'RF_DIR_PATH' in CONFIG :
        RF_DIR_PATH = CONFIG['RF_DIR_PATH']
    if 'OUTPUT_DIR' in CONFIG :
        OUTPUT_DIR = CONFIG['OUTPUT_DIR']

    if 'MYSQL_HOST' in CONFIG :
        MYSQL_HOST = CONFIG['MYSQL_HOST']
    if 'MYSQL_USER' in CONFIG :
        MYSQL_USER = CONFIG['MYSQL_USER']
    if 'MYSQL_DB' in CONFIG :
        MYSQL_DB = CONFIG['MYSQL_DB']
    if 'MYSQL_PASSWORD' in CONFIG :
        MYSQL_PASSWORD = CONFIG['MYSQL_PASSWORD']

    date = ''
    time = ''
    forceInsert = False
    allInsert = True
    rainfallInsert = False
    dischargeInsert = False
    waterlevelInsert = False
    waterlevelOutSuffix = ''
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hd:t:frew", ["help", "date=", "time=", "force", "rainfall", "discharge", "waterlevel", "wl_out_suffix="])
    except getopt.GetoptError:          
        usage()                        
        sys.exit(2)                     
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()                     
            sys.exit()           
        elif opt in ("-d", "--date"):
            date = arg
        elif opt in ("-t", "--time"):
            time = arg
        elif opt in ("-f", "--force"):
            forceInsert = True
        elif opt in ("-r", "--rainfall"):
            rainfallInsert = True
        elif opt in ("-e", "--discharge"):
            dischargeInsert = True
        elif opt in ("-w", "--waterlevel"):
            waterlevelInsert = True
        elif opt in ("--wl_out_suffix"):
            waterlevelOutSuffix = arg

    if rainfallInsert or dischargeInsert or waterlevelInsert :
        allInsert = False

    # Default run for current day
    now = datetime.datetime.now()
    if date :
        now = datetime.datetime.strptime(date, '%Y-%m-%d')
    date = now.strftime("%Y-%m-%d")

    if not waterlevelOutSuffix :
        waterlevelOutSuffix = date

    print('CSVTODAT startTime:', datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
except Exception as e :
    traceback.print_exc()

def storeDischarge(adapter):
    stations = ['Hanwella']
    types = [
        'Forecast-0-d', 
        'Forecast-1-d-after', 
        'Forecast-2-d-after', 
        'Forecast-3-d-after',
        'Forecast-4-d-after',
        'Forecast-5-d-after'
    ]
    metaData = {
        'station': 'Hanwella',
        'variable': 'Discharge',
        'unit': 'm3/s',
        'type': 'Forecast',
        'source': 'HEC-HMS',
        'name': 'HEC-HMS %s' % (date),
        'start_date': '2017-05-01 00:00:00',
        'end_date': '2017-05-03 23:00:00'
    }

    fileName = DISCHARGE_CSV_FILE.split('.', 1)
    fileName = "%s-%s.%s" % (fileName[0], date, fileName[1])
    DISCHARGE_CSV_FILE_PATH = "%s/%s" % (OUTPUT_DIR, fileName)
    if not os.path.exists(DISCHARGE_CSV_FILE_PATH):
        print('Discharge > Unable to find file : ', DISCHARGE_CSV_FILE_PATH)
        return None

    print('Discharge > store %s on startTime: %s' % (DISCHARGE_CSV_FILE_PATH, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    csvReader = csv.reader(open(DISCHARGE_CSV_FILE_PATH, 'r'), delimiter=',', quotechar='|')
    timeseries = list(csvReader)[DISCHARGE_NUM_METADATA_LINES:]

    print('Start Date :', timeseries[0][0])
    print('End Date :', timeseries[-1][0])
    startDateTime = datetime.datetime.strptime(timeseries[0][0], '%Y:%m:%d %H:%M:%S')
    endDateTime = datetime.datetime.strptime(timeseries[-1][0], '%Y:%m:%d %H:%M:%S')

    dischargeMeta = dict(metaData)
    dischargeMeta['start_date'] = startDateTime.strftime("%Y-%m-%d %H:%M:%S")
    dischargeMeta['end_date'] = endDateTime.strftime("%Y-%m-%d %H:%M:%S")

    for i in range(0, 6) :
        dischargeMeta['type'] = types[i]
        eventId = adapter.getEventId(dischargeMeta)
        if eventId is None :
            eventId = adapter.createEventId(dischargeMeta)
            print('HASH SHA256 created: ', eventId)
        else :
            print('HASH SHA256 exists: ', eventId)
        
        # for l in timeseries[:3] + timeseries[-2:] :
        #     print(l)
        rowCount = adapter.insertTimeseries(eventId, timeseries[i*DAY_INTERVAL:(i+1)*DAY_INTERVAL], True)
        print('%s rows inserted.' % rowCount)


def storeRainfall(adapter):
    for guage in RAIN_GUAGES :
        for filename in glob.glob(os.path.join(RF_DIR_PATH, '%s-%s*.txt' % (guage, date))):
            if not os.path.exists(filename):
                print('Discharge > Unable to find file : ', filename)
                break

            print('Rainfall > store %s on startTime: %s' % (filename, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            csvGuage = csv.reader(open(filename, 'r'), delimiter=' ', skipinitialspace=True)
            timeseries = list(csvGuage)

            print('Start Date :', timeseries[0][0])
            print('End Date :', timeseries[-1][0])
            startDateTime = datetime.datetime.strptime(timeseries[0][0], '%Y-%m-%d_%H:%M:%S')
            endDateTime = datetime.datetime.strptime(timeseries[-1][0], '%Y-%m-%d_%H:%M:%S')

            metaData = {
                'station': guage,
                'variable': 'Precipitation',
                'unit': 'mm',
                'type': 'Forecast',
                'source': 'WRF',
                'name': 'WRF %s' % (date),
                'start_date': startDateTime.strftime("%Y-%m-%d %H:%M:%S"),
                'end_date': endDateTime.strftime("%Y-%m-%d %H:%M:%S")
            }
            eventId = adapter.getEventId(metaData)
            if eventId is None :
                print('eventId is None. Creating a New.')
                eventId = adapter.createEventId(metaData)
                print('HASH SHA256 : ', eventId)
                for l in timeseries[:3:-2] :
                    print(l)
                rowCount = adapter.insertTimeseries(eventId, timeseries)
                print('%s rows inserted.' % rowCount)
            else:
                print('HASH SHA256 : ', eventId)
                if forceInsert :
                    deleteCount = adapter.deleteTimeseries(eventId)
                    print('%s rows deleted.' % deleteCount)
                    for l in timeseries[:3] + timeseries[-2:] :
                        print(l)
                    eventId = adapter.createEventId(metaData)
                    rowCount = adapter.insertTimeseries(eventId, timeseries)
                    print('%s rows inserted.' % rowCount)
                else :
                    print('Timeseries already exists. User -f arg to override existing timeseries.')

def storeWaterlevel(adapter):
    print('\nStoring Waterlevels :::')
    WATER_LEVEL_DIR_PATH = os.path.join(OUTPUT_DIR, '%s-%s' % (WATER_LEVEL_DIR_NAME, waterlevelOutSuffix))
    if not os.path.exists(WATER_LEVEL_DIR_PATH):
        print('Discharge > Unable to find dir : ', WATER_LEVEL_DIR_PATH)
        return

    for filename in glob.glob(os.path.join(WATER_LEVEL_DIR_PATH, '*')):
            if not os.path.exists(filename):
                print('Discharge > Unable to find file : ', filename)
                break
            print('>>>>', filename)


adapter = mysqladapter(host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD, db=MYSQL_DB)

if rainfallInsert or allInsert :
    storeRainfall(adapter)

if dischargeInsert or allInsert :
    storeDischarge(adapter)

if waterlevelInsert or allInsert :
    storeWaterlevel(adapter)

