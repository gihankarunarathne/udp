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
    --wl-out-suffix Suffix for 'water_level-<SUFFIX>' output directories. 
                    Default is 'water_level-<YYYY-MM-DD>' same as -d option value.
    --rainfall-path     Directory path which contains the Rainfall timeseries.
    --discharge-path    Directory path which contains the Discharge timeseries.
    --waterlevel-path   Directory path which contains the WaterLevel timeseries directories.
                        E.g: '<waterlevel-path>/water_level-2017-05-27'.
"""
    print(usageText)

try :
    CONFIG = json.loads(open('CONFIG.json').read())
    # print('Config :: ', CONFIG)

    DISCHARGE_NUM_METADATA_LINES = 2
    DISCHARGE_CSV_FILE = 'DailyDischarge.csv'
    RAIN_CSV_FILE = 'DailyRain.csv'
    WATER_LEVEL_DIR_NAME = 'water_level'
    
    OUTPUT_DIR = './OUTPUT'
    RF_DIR_PATH = '/mnt/disks/wrf-mod/OUTPUT/'
    DIS_OUTPUT_DIR = OUTPUT_DIR
    WL_OUTPUT_DIR = OUTPUT_DIR

    DIS_RESOLUTION = 24 # In 1 hours
    RF_RESOLUTION = 24 # In 1 hours
    WL_RESOLUTION = 24 * 4 # In 15 mins

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
        DIS_OUTPUT_DIR = OUTPUT_DIR
        WL_OUTPUT_DIR = OUTPUT_DIR

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
        opts, args = getopt.getopt(sys.argv[1:], "hd:t:frew", [
            "help", "date=", "time=", "force",
            "rainfall", "discharge", "waterlevel",
            "wl-out-suffix=", "rainfall-path=", "discharge-path=", "waterlevel-path="
        ])
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
        elif opt in ("--wl-out-suffix"):
            waterlevelOutSuffix = arg
        elif opt in ("--rainfall-path"):
            RF_DIR_PATH = arg
            print('WARN: Using custom Rainfall Path :', RF_DIR_PATH)
        elif opt in ("--discharge-path"):
            DIS_OUTPUT_DIR = arg
            print('WARN: Using custom Discharge Path :', DIS_OUTPUT_DIR)
        elif opt in ("--waterlevel-path"):
            WL_OUTPUT_DIR = arg
            print('WARN: Using custom WaterLevel Path :', WL_OUTPUT_DIR)

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
    if forceInsert :
        print('WARNING: Force Insert enabled')
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
        'type': 'Forecast-0-d',
        'source': 'HEC-HMS',
        'name': 'Cloud Continuous',
        'start_date': '2017-05-01 00:00:00',
        'end_date': '2017-05-03 23:00:00'
    }

    fileName = DISCHARGE_CSV_FILE.split('.', 1)
    fileName = "%s-%s.%s" % (fileName[0], date, fileName[1])
    DISCHARGE_CSV_FILE_PATH = "%s/%s" % (DIS_OUTPUT_DIR, fileName)
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
            if not forceInsert :
                print('\n')
                continue
        
        # for l in timeseries[:3] + timeseries[-2:] :
        #     print(l)
        rowCount = adapter.insertTimeseries(eventId, timeseries[i*DIS_RESOLUTION:(i+1)*DIS_RESOLUTION], forceInsert)
        print('%s rows inserted.\n' % rowCount)


def storeRainfall(adapter):
    stations = ['Attanagalla', 'Colombo', 'Daraniyagala', 'Glencourse', 'Hanwella', 'Holombuwa', 'Kitulgala', 'Norwood']
    types = ['Forecast-0-d', 'Forecast-1-d-after', 'Forecast-2-d-after']
    metaData = {
        'station': 'Hanwella',
        'variable': 'Precipitation',
        'unit': 'mm',
        'type': 'Forecast-0-d',
        'source': 'WRF',
        'name': 'Cloud-1',
        'start_date': '2017-05-01 00:00:00',
        'end_date': '2017-05-03 23:00:00'
    }

    for station in stations :
        for filename in glob.glob(os.path.join(RF_DIR_PATH, '%s-%s*.txt' % (station, date))):
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

            rainfallMeta = dict(metaData)
            rainfallMeta['station'] = station
            rainfallMeta['start_date'] = startDateTime.strftime("%Y-%m-%d %H:%M:%S")
            rainfallMeta['end_date'] = endDateTime.strftime("%Y-%m-%d %H:%M:%S")

            for i in range(0, 3) :
                rainfallMeta['type'] = types[i]
                eventId = adapter.getEventId(rainfallMeta)
                if eventId is None :
                    eventId = adapter.createEventId(rainfallMeta)
                    print('HASH SHA256 created: ', eventId)
                else :
                    print('HASH SHA256 exists: ', eventId)
                    if not forceInsert :
                        print('\n')
                        continue
                
                # for l in timeseries[:3] + timeseries[-2:] :
                #     print(l)
                rowCount = adapter.insertTimeseries(eventId, timeseries[i*RF_RESOLUTION:(i+1)*RF_RESOLUTION], forceInsert)
                print('%s rows inserted.\n' % rowCount)


def storeWaterlevel(adapter):
    print('\nStoring Waterlevels :::')
    stations = [
        "Ambathale",
        "Madiwela Out",
        "Salalihini Out",
        "Salalihini Out 2",
        "Kittampahuwa Bridge",
        "Kittampahuwa Out",
        "Kittampahuwa Out 2",
        "N Street",
        "N Street 2",
        "Kolonnawa CNL 1",
        "Kolonnawa CNL 2",
        "Kolonnawa CNL 3",
        "Kolonnawa CNL 4",
        "Parliament Lake Out",
        "Parliament Lake",
        "Parliament Lake 2",
        "Parliament Upstream",
        "Ahangama",
        "Madiwela US",
        "Heen Ela",
        "Torington",
        "Wellawatta 1",
        "Wellawatta 2",
        "Wellawatta 3",
        "Dehiwala 1",
        "Dehiwala 2"
    ]
    types = [
        'Forecast-0-d', 
        'Forecast-1-d-after', 
        'Forecast-2-d-after', 
        'Forecast-3-d-after',
        'Forecast-4-d-after',
        'Forecast-5-d-after'
    ]
    metaData = {
        'station': 'Ambathale',
        'variable': 'Precipitation',
        'unit': 'mm',
        'type': 'Forecast-0-d',
        'source': 'WRF',
        'name': 'Cloud-1',
        'start_date': '2017-05-01 00:00:00',
        'end_date': '2017-05-03 23:00:00'
    }

    WATER_LEVEL_DIR_PATH = os.path.join(WL_OUTPUT_DIR, '%s-%s' % (WATER_LEVEL_DIR_NAME, waterlevelOutSuffix))
    if not os.path.exists(WATER_LEVEL_DIR_PATH):
        print('Discharge > Unable to find dir : ', WATER_LEVEL_DIR_PATH)
        return

    for station in stations :
        for filename in glob.glob(os.path.join(WATER_LEVEL_DIR_PATH, '%s-%s-*.txt' % (WATER_LEVEL_DIR_NAME, station.replace(' ', '_')))):
            if not os.path.exists(filename):
                print('Discharge > Unable to find file : ', filename)
                break

            print('Waterlevel > store %s on startTime: %s' % (filename, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            csvReader = csv.reader(open(filename, 'r'), delimiter=',', quotechar='|')
            timeseries = list(csvReader)

            print('Start Date :', timeseries[0][0])
            print('End Date :', timeseries[-1][0])
            startDateTime = datetime.datetime.strptime(timeseries[0][0], '%Y-%m-%d %H:%M:%S')
            endDateTime = datetime.datetime.strptime(timeseries[-1][0], '%Y-%m-%d %H:%M:%S')

            waterlevelMeta = dict(metaData)
            waterlevelMeta['station'] = station.replace(' ', '-')
            waterlevelMeta['start_date'] = startDateTime.strftime("%Y-%m-%d %H:%M:%S")
            waterlevelMeta['end_date'] = endDateTime.strftime("%Y-%m-%d %H:%M:%S")

            for i in range(0, 6) :
                waterlevelMeta['type'] = types[i]
                eventId = adapter.getEventId(waterlevelMeta)
                if eventId is None :
                    eventId = adapter.createEventId(waterlevelMeta)
                    print('HASH SHA256 created: ', eventId)
                else :
                    print('HASH SHA256 exists: ', eventId)
                    if not forceInsert :
                        print('\n')
                        continue
                
                # for l in timeseries[:3] + timeseries[-2:] :
                #     print(l)
                rowCount = adapter.insertTimeseries(eventId, timeseries[i*WL_RESOLUTION:(i+1)*WL_RESOLUTION], forceInsert)
                print('%s rows inserted.\n' % rowCount)


adapter = mysqladapter(host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD, db=MYSQL_DB)

if rainfallInsert or allInsert :
    storeRainfall(adapter)

if dischargeInsert or allInsert :
    storeDischarge(adapter)

if waterlevelInsert or allInsert :
    storeWaterlevel(adapter)

