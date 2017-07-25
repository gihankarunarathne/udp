#!/usr/bin/python3

from curwmysqladapter import mysqladapter
import sys, traceback, csv, json, datetime, getopt, glob, os, copy
import numpy as np

from LIBFLO2DWATERLEVELGRID import getGridBoudary
from LIBFLO2DWATERLEVELGRID import getCellGrid

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
-g  --waterlevelgrid    Store waterlevel grid specifically. Ignore others if not mentioned.
    --flo2d-stations    Store FLO2D model stations
    --wl-out-suffix Suffix for 'water_level-<SUFFIX>' output directories. 
                    Default is 'water_level-<YYYY-MM-DD>' same as -d option value.
    --rainfall-path     Directory path which contains the Rainfall timeseries.
    --discharge-path    Directory path which contains the Discharge timeseries.
    --waterlevel-path   Directory path which contains the WaterLevel timeseries directories.
                        E.g: '<waterlevel-path>/water_level-2017-05-27'.
    --waterlevelgrid-path   Directory path which contains the WaterLevel timeseries directories.
                            E.g: '<waterlevelgrid-path>/water_level_grid-2017-05-27'.
-n                  New Line character -> None, '', '\\n', '\\r', and '\\r\\n'. Default is '\\n'.
"""
    print(usageText)

try :
    # print('Config :: ', CONFIG)
    INIT_DIR = os.getcwd()
    ROOT_DIR = os.path.dirname(os.path.realpath(__file__))
    os.chdir(ROOT_DIR)

    CONFIG = json.loads(open(os.path.join(ROOT_DIR, 'CONFIG.json')).read())

    NEW_LINE = '\n'
    DISCHARGE_NUM_METADATA_LINES = 2
    DISCHARGE_CSV_FILE = 'DailyDischarge.csv'
    RAIN_CSV_FILE = 'DailyRain.csv'
    WATER_LEVEL_DIR_NAME = 'water_level'
    WATER_LEVEL_GRID_DIR_NAME = 'water_level_grid'
    
    OUTPUT_DIR = './OUTPUT'
    RF_DIR_PATH = '/mnt/disks/wrf-mod/OUTPUT/'
    DIS_OUTPUT_DIR = OUTPUT_DIR
    WL_OUTPUT_DIR = OUTPUT_DIR
    WL_GRID_OUTPUT_DIR = OUTPUT_DIR

    DIS_RESOLUTION = 24 # In 1 hours
    RF_RESOLUTION = 24 # In 1 hours
    WL_RESOLUTION = 24 * 4 # In 15 mins
    WL_GRID_RESOLUTION = 24 # In 60 mins
    WL_GRID_MISSING_VALUE = -9

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
        WL_GRID_OUTPUT_DIR = OUTPUT_DIR

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
    waterlevelGridInsert = False
    flo2dStationsInsert = False
    waterlevelOutSuffix = ''
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hd:t:frewgn:", [
            "help", "date=", "time=", "force",
            "rainfall", "discharge", "waterlevel", "waterlevelgrid", "flo2d-stations",
            "wl-out-suffix=", "rainfall-path=", "discharge-path=", "waterlevel-path=", "waterlevelgrid-path="
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
        elif opt in ("-g", "--waterlevelgrid"):
            waterlevelGridInsert = True
        elif opt in ("--flo2d-stations"):
            flo2dStationsInsert = True
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
        elif opt in ("--waterlevelgrid-path"):
            WL_GRID_OUTPUT_DIR = arg
            print('WARN: Using custom WaterLevel Grid Path :', WL_GRID_OUTPUT_DIR)
        elif opt in ("-n"):
            NEW_LINE = arg

    if rainfallInsert or dischargeInsert or waterlevelInsert or waterlevelGridInsert or flo2dStationsInsert :
        allInsert = False

    # Default run for current day
    now = datetime.datetime.now()
    if date :
        now = datetime.datetime.strptime(date, '%Y-%m-%d')
    date = now.strftime("%Y-%m-%d")

    if not waterlevelOutSuffix :
        waterlevelOutSuffix = date

    print('CSVTODAT startTime:', datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'on', ROOT_DIR)
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
        'station': stations[0],
        'variable': 'Discharge',
        'unit': 'm3/s',
        'type': types[0],
        'source': 'HEC-HMS',
        'name': 'Cloud Continuous',
    }

    fileName = DISCHARGE_CSV_FILE.rsplit('.', 1)
    fileName = "%s-%s.%s" % (fileName[0], date, fileName[1])
    # DISCHARGE_CSV_FILE_PATH = "%s/%s" % (DIS_OUTPUT_DIR, fileName)
    DISCHARGE_CSV_FILE_PATH = os.path.join(DIS_OUTPUT_DIR, fileName)
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

    dischargeMeta = copy.deepcopy(metaData)
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
                print('Timeseries already exists. User --force to update the existing.\n')
                continue
        
        # for l in timeseries[:3] + timeseries[-2:] :
        #     print(l)
        rowCount = adapter.insertTimeseries(eventId, timeseries[i*DIS_RESOLUTION:(i+1)*DIS_RESOLUTION], forceInsert)
        print('%s rows inserted.\n' % rowCount)


def storeRainfall(adapter):
    stations = ['Attanagalla', 'Colombo', 'Daraniyagala', 'Glencourse', 'Hanwella', 'Holombuwa', 'Kitulgala', 'Norwood']
    types = ['Forecast-0-d', 'Forecast-1-d-after', 'Forecast-2-d-after']
    metaData = {
        'station': stations[0],
        'variable': 'Precipitation',
        'unit': 'mm',
        'type': types[0],
        'source': 'WRF',
        'name': 'Cloud-1',
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

            rainfallMeta = copy.deepcopy(metaData)
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
                        print('Timeseries already exists. User --force to update the existing.\n')
                        continue
                
                # for l in timeseries[:3] + timeseries[-2:] :
                #     print(l)
                rowCount = adapter.insertTimeseries(eventId, timeseries[i*RF_RESOLUTION:(i+1)*RF_RESOLUTION], forceInsert)
                print('%s rows inserted.\n' % rowCount)


def storeWaterlevel(adapter):
    print('\nStoring Waterlevels :::')
    stations = [
        "N'Street-River",
        "N'Street-Canal",
        "Wellawatta",
        "Dehiwala",
        "Parliment Lake-Out",
        "Parliment Lake",
        "Madiwela-US",
        "Ambathale",
        "Madiwela-Out",
        "Salalihini-River",
        "Salalihini-Canal",
        "Kittampahuwa-River",
        "kittampahuwa-Out",
        "Kolonnawa Canal",
        "Heen Ela",
        "Torington",
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
        'station': stations[0],
        'variable': 'Waterlevel',
        'unit': 'm',
        'type': types[0],
        'source': 'FLO2D',
        'name': 'Cloud-1',
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
            csvReader = csv.reader(open(filename, 'r', newline=NEW_LINE), delimiter=',', quotechar='|')
            timeseries = list(csvReader)

            print('Start Date :', timeseries[0][0])
            print('End Date :', timeseries[-1][0])
            startDateTime = datetime.datetime.strptime(timeseries[0][0], '%Y-%m-%d %H:%M:%S')
            endDateTime = datetime.datetime.strptime(timeseries[-1][0], '%Y-%m-%d %H:%M:%S')

            waterlevelMeta = copy.deepcopy(metaData)
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
                    waterlevelMetaQuery = copy.deepcopy(metaData)
                    waterlevelMetaQuery['station'] = station.replace(' ', '-')
                    waterlevelMetaQuery['type'] = types[i]

                    dailyTimeseries = timeseries[i*WL_RESOLUTION:(i+1)*WL_RESOLUTION]
                    dailyStartDateTime = datetime.datetime.strptime(dailyTimeseries[0][0], '%Y-%m-%d %H:%M:%S')
                    dailyEndDateTime = datetime.datetime.strptime(dailyTimeseries[-1][0], '%Y-%m-%d %H:%M:%S')
                    opts = {
                        'from': dailyStartDateTime.strftime("%Y-%m-%d %H:%M:%S"),
                        'to': dailyEndDateTime.strftime("%Y-%m-%d %H:%M:%S")
                    }
                    existingTimeseries = adapter.retrieveTimeseries(waterlevelMetaQuery, opts)
                    if len(existingTimeseries[0]['timeseries']) > 0 and not forceInsert:
                        print('Timeseries already exists. User --force to update the existing.\n')
                        continue
                
                # for l in timeseries[:3] + timeseries[-2:] :
                #     print(l)
                rowCount = adapter.insertTimeseries(eventId, timeseries[i*WL_RESOLUTION:(i+1)*WL_RESOLUTION], forceInsert)
                print('%s rows inserted.\n' % rowCount)

def storeFLO2DStations(adapter):
    print('\nStoring FLO2D Stations :::')

    bufsize = 65536
    stationIDOffset = 1000
    with open('./META_FLO2D/CADPTS.DAT') as infile:
        stations = []
        while True:
            lines = infile.readlines(bufsize)

            if not lines:
                break
            for line in lines:
                s = line.split()
                if len(s) > 0 :
                    cellId = int(s[0])
                    stations.append([stationIDOffset + cellId, 'FLO2D %s' % cellId, s[1], s[2]])
                    print('FLO2D Cell:', cellId, 'with latitude: %s, longitude: %s -> inserted as `FLO2D %s`' % (s[1], s[2], cellId))

        # for station in stations[:3] + stations[-2:] :
        #     print(station)
        rowCount = adapter.createStations(stations)
        print('%s stations inserted.\n' % rowCount)

def storeWaterlevelGrid(adapter):
    print('\nStoring Waterlevel Grid :::')

    bufsize = 65536
    stationIDOffset = 1000
    CELLS = []
    with open('./META_FLO2D/CADPTS.DAT') as infile:
        while True:
            lines = infile.readlines(bufsize)

            if not lines:
                break
            for line in lines:
                s = line.split()
                if len(s) > 0 :
                    cellId = int(s[0])
                    CELLS.append(cellId)

    types = [
        'Forecast-0-d',
        'Forecast-1-d-after',
        'Forecast-2-d-after',
        'Forecast-3-d-after',
        'Forecast-4-d-after',
        'Forecast-5-d-after'
    ]
    metaData = {
        'station': 'FLO2D %s' % CELLS[0],
        'variable': 'Waterlevel',
        'unit': 'm',
        'type': types[0],
        'source': 'FLO2D',
        'name': 'Cloud-1',
    }

    WATER_LEVEL_GRID_DIR_PATH = os.path.join(WL_GRID_OUTPUT_DIR, '%s-%s' % (WATER_LEVEL_GRID_DIR_NAME, waterlevelOutSuffix))
    if not os.path.exists(WATER_LEVEL_GRID_DIR_PATH):
        print('Discharge > Unable to find dir : ', WATER_LEVEL_GRID_DIR_PATH)
        return

    boundary    = getGridBoudary()
    CellGrid    = getCellGrid(boundary)
    waterLevelGridSeriesDict = dict.fromkeys(CELLS, [])

    for fileName in sorted(glob.glob(os.path.join(WATER_LEVEL_GRID_DIR_PATH, '%s-*.asc' % (WATER_LEVEL_GRID_DIR_NAME)))) :
        if not os.path.exists(fileName):
            print('Discharge > Unable to find file : ', fileName)
            break

        # Extract time from fileName
        ascFileName = fileName.rsplit('/', 1)[-1]
        dateTimeStr = ascFileName[len(WATER_LEVEL_GRID_DIR_NAME)+1:-4]
        dateTime = datetime.datetime.strptime(dateTimeStr, '%Y-%m-%d_%H-%M-%S')

        ascii_grid = np.loadtxt(fileName, skiprows=6)
        for cellNo in CELLS :
            i, j = CellGrid[cellNo]
            tmpTS = waterLevelGridSeriesDict[cellNo][:]
            tmpTS.append([dateTime.strftime("%Y-%m-%d %H:%M:%S"), ascii_grid[j][i] ])
            waterLevelGridSeriesDict[cellNo] = tmpTS
        print('Scanned Waterlevel Grid file :', ascFileName)

    for station in CELLS :
        timeseries = waterLevelGridSeriesDict[station]

        startDateTime = datetime.datetime.strptime(timeseries[0][0], '%Y-%m-%d %H:%M:%S')
        baseTime = datetime.datetime.strptime(date, '%Y-%m-%d')
        if(startDateTime > baseTime) :
            print('Adding base time into the top of timeseries')
            timeseries = [[baseTime.strftime("%Y-%m-%d %H:%M:%S"), WL_GRID_MISSING_VALUE]] + timeseries[:]

        print('Start Date :', timeseries[0][0])
        print('End Date :', timeseries[-1][0])
        startDateTime = datetime.datetime.strptime(timeseries[0][0], '%Y-%m-%d %H:%M:%S')
        endDateTime = datetime.datetime.strptime(timeseries[-1][0], '%Y-%m-%d %H:%M:%S')

        waterlevelGridMeta = copy.deepcopy(metaData)
        waterlevelGridMeta['station'] = 'FLO2D %s' % station
        waterlevelGridMeta['start_date'] = startDateTime.strftime("%Y-%m-%d %H:%M:%S")
        waterlevelGridMeta['end_date'] = endDateTime.strftime("%Y-%m-%d %H:%M:%S")

        for i in range(0, 6) :
            waterlevelGridMeta['type'] = types[i]
            eventId = adapter.getEventId(waterlevelGridMeta)
            if eventId is None :
                eventId = adapter.createEventId(waterlevelGridMeta)
                print('HASH SHA256 created: ', eventId)
            else :
                print('HASH SHA256 exists: ', eventId)
                waterlevelGridMetaQuery = copy.deepcopy(metaData)
                waterlevelGridMetaQuery['station'] = 'FLO2D %s' % station
                waterlevelGridMetaQuery['type'] = types[i]

                dailyTimeseries = timeseries[i*WL_GRID_RESOLUTION:(i+1)*WL_GRID_RESOLUTION]
                dailyStartDateTime = datetime.datetime.strptime(dailyTimeseries[0][0], '%Y-%m-%d %H:%M:%S')
                dailyEndDateTime = datetime.datetime.strptime(dailyTimeseries[-1][0], '%Y-%m-%d %H:%M:%S')
                opts = {
                    'from': dailyStartDateTime.strftime("%Y-%m-%d %H:%M:%S"),
                    'to': dailyEndDateTime.strftime("%Y-%m-%d %H:%M:%S")
                }
                existingTimeseries = adapter.retrieveTimeseries(waterlevelGridMetaQuery, opts)
                if len(existingTimeseries[0]['timeseries']) > 0 and not forceInsert:
                    print('Timeseries already exists. User --force to update the existing.\n')
                    continue

            # for l in timeseries[:3] + timeseries[-2:] :
            #     print(l)
            rowCount = adapter.insertTimeseries(eventId, timeseries[i*WL_GRID_RESOLUTION:(i+1)*WL_GRID_RESOLUTION], forceInsert)
            print('%s rows inserted.\n' % rowCount)



adapter = mysqladapter(host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD, db=MYSQL_DB)

if rainfallInsert or allInsert :
    storeRainfall(adapter)

if dischargeInsert or allInsert :
    storeDischarge(adapter)

if waterlevelInsert or allInsert :
    storeWaterlevel(adapter)

if waterlevelGridInsert or allInsert :
    storeWaterlevelGrid(adapter)

if flo2dStationsInsert :
    storeFLO2DStations(adapter)
