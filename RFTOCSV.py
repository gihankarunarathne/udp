#!/usr/bin/python3

import sys, traceback, datetime, os, glob, csv, json, getopt
from string import Template
from collections import OrderedDict
from curwmysqladapter import mysqladapter

def usage() :
    usageText = """
Usage: ./CSVTODAT.py [-d YYYY-MM-DD] [-t HH:MM:SS] [-h]

-h  --help          Show usage
-d  --date          Date in YYYY-MM-DD. Default is current date.
-t  --time          Time in HH:MM:SS. Default is current time.
    --start-date    Start date of timeseries which need to run the forecast in YYYY-MM-DD format. Default is same as -d(date).
    --start-time    Start time of timeseries which need to run the forecast in HH:MM:SS format. Default is same as -t(date).
-T  --tag           Tag to differential simultaneous Forecast Runs E.g. wrf1, wrf2 ...
    --wrf-rf        Path of WRF Rf(Rainfall) Directory. Otherwise using the `RF_DIR_PATH` from CONFIG.json
    --wrf-kub       Path of WRF kelani-upper-basin(KUB) Directory. Otherwise using the `KUB_DIR_PATH` from CONFIG.json
"""
    print(usageText)

def getObservedTimeseries(adapter, eventId, opts) :
    existingTimeseries = adapter.retrieveTimeseries([eventId], opts)
    newTimeseries = []
    if len(existingTimeseries) > 0 and len(existingTimeseries[0]['timeseries']) > 0 :
        existingTimeseries = existingTimeseries[0]['timeseries']
        prevDateTime = existingTimeseries[1][0]
        precSum = existingTimeseries[0][1]
        for tt in existingTimeseries :
            if prevDateTime.replace(minute=0, second=0, microsecond=0) == tt[0].replace(minute=0, second=0, microsecond=0) :
                precSum += tt[1] # TODO: If missing or minus -> ignore
                # TODO: Handle End of List
            else :
                newTimeseries.append([tt[0].replace(minute=0, second=0, microsecond=0), precSum])
                prevDateTime = tt[0]
                precSum = tt[1]

    return newTimeseries

try :
    CONFIG = json.loads(open('CONFIG.json').read())
    # print('Config :: ', CONFIG)
    RAIN_CSV_FILE = 'DailyRain.csv'
    RF_DIR_PATH = './WRF/RF/'
    KUB_DIR_PATH = './WRF/kelani-upper-basin'
    OUTPUT_DIR = './OUTPUT'
    # Kelani Upper Basin
    KUB_OBS_ID = 'ecc89f516b7c5aa8d2d06e07f4bdc293aeb957fd5272ad75385e7a2e5b9e3015'
    # Kelani Basin
    KB_OBS_ID = '0e7bf64861fe493a7ea9ac4cfafd710d2e5a8f06b9824fb68d26b064babb9800'

    MYSQL_HOST="localhost"
    MYSQL_USER="root"
    MYSQL_DB="curw"
    MYSQL_PASSWORD=""

    if 'RAIN_CSV_FILE' in CONFIG :
        RAIN_CSV_FILE = CONFIG['RAIN_CSV_FILE']
    if 'RF_DIR_PATH' in CONFIG :
        RF_DIR_PATH = CONFIG['RF_DIR_PATH']
    if 'KUB_DIR_PATH' in CONFIG :
        KUB_DIR_PATH = CONFIG['KUB_DIR_PATH']
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
    startDate = ''
    startTime = ''
    tag=''
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hd:t:T:", [
            "help", "date=", "time=", "start-date=", "start-time=", "wrf-rf=", "wrf-kub=", "tag="
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
        elif opt in ("--start-date"):
            startDate = arg
        elif opt in ("--start-time"):
            startTime = arg
        elif opt in ("--wrf-rf"):
            RF_DIR_PATH = arg
        elif opt in ("--wrf-kub"):
            KUB_DIR_PATH = arg
        elif opt in ("-T", "--tag"):
            tag = arg

    UPPER_CATCHMENT_WEIGHTS = {
        # 'Attanagalla'   : 1/7,    # 1
        'Daraniyagala'  : 0.146828, # 2
        'Glencourse'    : 0.208938, # 3
        'Hanwella'      : 0.078722, # 4
        'Holombuwa'     : 0.163191, # 5
        'Kitulgala'     : 0.21462,  # 6
        'Norwood'       : 0.187701  # 7
    }
    UPPER_CATCHMENTS = UPPER_CATCHMENT_WEIGHTS.keys()

    KELANI_UPPER_BASIN_WEIGHTS = {
        'mean-rf'       : 1
    }
    KELANI_UPPER_BASIN = KELANI_UPPER_BASIN_WEIGHTS.keys()

    LOWER_CATCHMENT_WEIGHTS = {
        'Colombo'       :  1
    }
    LOWER_CATCHMENTS = LOWER_CATCHMENT_WEIGHTS.keys()

    # Default run for current day
    modelState = datetime.datetime.now()
    if date :
        modelState = datetime.datetime.strptime(date, '%Y-%m-%d')
    date = modelState.strftime("%Y-%m-%d")
    if time :
        modelState = datetime.datetime.strptime('%s %s' % (date, time), '%Y-%m-%d %H:%M:%S')
    time = modelState.strftime("%H:%M:%S")

    startDateTime = datetime.datetime.now()
    if startDate :
        startDateTime = datetime.datetime.strptime(startDate, '%Y-%m-%d')
    else :
        startDateTime = datetime.datetime.strptime(date, '%Y-%m-%d')

    if startTime :
        startDateTime = datetime.datetime.strptime('%s %s' % (startDate, startTime), '%Y-%m-%d %H:%M:%S')

    startDate = startDateTime.strftime("%Y-%m-%d")
    startTime = startDateTime.strftime("%H:%M:%S")


    print('RFTOCSV startTime:', datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print(' RFTOCSV run for', date, '@', time, tag)
    print(' With Custom starting', startDate, '@', startTime)

    UPPER_THEISSEN_VALUES = OrderedDict()
    for catchment in UPPER_CATCHMENTS :
        for filename in glob.glob(os.path.join(RF_DIR_PATH, '%s-%s*.txt' % (catchment, date) )):
            print('Start Operating on (Upper) ', filename)
            csvCatchment = csv.reader(open(filename, 'r'), delimiter=' ', skipinitialspace=True)
            csvCatchment = list(csvCatchment)
            for row in csvCatchment :
                # print(row[0].replace('_', ' '), row[1].strip(' \t'))
                d = datetime.datetime.strptime(row[0].replace('_', ' '), '%Y-%m-%d %H:%M:%S')
                key = d.timestamp()
                if key not in UPPER_THEISSEN_VALUES :
                    UPPER_THEISSEN_VALUES[key] = 0
                UPPER_THEISSEN_VALUES[key] += float(row[1].strip(' \t')) * UPPER_CATCHMENT_WEIGHTS[catchment]

    KELANI_UPPER_BASIN_VALUES = OrderedDict()
    for catchment in KELANI_UPPER_BASIN :
        for filename in glob.glob(os.path.join(KUB_DIR_PATH, catchment+'-'+date+'*.txt')):
            print('Start Operating on (Kelani Upper Basin) ', filename)
            csvCatchment = csv.reader(open(filename, 'r'), delimiter=' ', skipinitialspace=True)
            csvCatchment = list(csvCatchment)
            for row in csvCatchment :
                # print(row[0].replace('_', ' '), row[1].strip(' \t'))
                d = datetime.datetime.strptime(row[0].replace('_', ' '), '%Y-%m-%d %H:%M:%S')
                key = d.timestamp()
                if key not in KELANI_UPPER_BASIN_VALUES :
                    KELANI_UPPER_BASIN_VALUES[key] = 0
                KELANI_UPPER_BASIN_VALUES[key] += float(row[1].strip(' \t')) * KELANI_UPPER_BASIN_WEIGHTS[catchment]

    LOWER_THEISSEN_VALUES = OrderedDict()
    for lowerCatchment in LOWER_CATCHMENTS :
        for filename in glob.glob(os.path.join(RF_DIR_PATH, lowerCatchment+'-'+date+'*.txt')):
            print('Start Operating on (Lower) ', filename)
            csvCatchment = csv.reader(open(filename, 'r'), delimiter=' ', skipinitialspace=True)
            csvCatchment = list(csvCatchment)
            for row in csvCatchment :
                # print(row[0].replace('_', ' '), row[1].strip(' \t'))
                d = datetime.datetime.strptime(row[0].replace('_', ' '), '%Y-%m-%d %H:%M:%S')
                key = d.timestamp()
                if key not in LOWER_THEISSEN_VALUES :
                    LOWER_THEISSEN_VALUES[key] = 0
                LOWER_THEISSEN_VALUES[key] += float(row[1].strip(' \t')) * LOWER_CATCHMENT_WEIGHTS[lowerCatchment]

    # Get Observed Data
    adapter = mysqladapter(host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD, db=MYSQL_DB)
    opts = {
        'from': startDateTime.strftime("%Y-%m-%d %H:%M:%S"),
        'to': modelState.strftime("%Y-%m-%d %H:%M:%S")
    }
    KUB_Timeseries = getObservedTimeseries(adapter, KUB_OBS_ID, opts)
    # print('KUB_Timeseries::', KUB_Timeseries)
    KB_Timeseries = getObservedTimeseries(adapter, KB_OBS_ID, opts)
    # print('KB_Timeseries::', KB_Timeseries)

    print('Finished processing files. Start Writing Theissen polygon avg in to CSV')
    # print(UPPER_THEISSEN_VALUES)
    fileName = RAIN_CSV_FILE.rsplit('.', 1)
    fileName = '{name}-{date}{tag}.{extention}'.format(name=fileName[0], date=date, tag='.'+tag if tag else '', extention=fileName[1])
    RAIN_CSV_FILE_PATH = os.path.join(OUTPUT_DIR, fileName)
    csvWriter = csv.writer(open(RAIN_CSV_FILE_PATH, 'w'), delimiter=',', quotechar='|')
    # Write Metadata https://publicwiki.deltares.nl/display/FEWSDOC/CSV
    csvWriter.writerow(['Location Names', 'Awissawella', 'Colombo'])
    csvWriter.writerow(['Location Ids', 'Awissawella', 'Colombo'])
    csvWriter.writerow(['Time', 'Rainfall', 'Rainfall'])

    # Insert available observed data
    lastObsDateTime = startDateTime
    for kub_tt in KUB_Timeseries :
        # look for same time value in Kelani Basin
        kb_tt = kub_tt # TODO: Better to replace with missing ???
        for sub_tt in KB_Timeseries :
            if sub_tt[0] == kub_tt[0] :
                kb_tt = sub_tt
                break

        csvWriter.writerow([kub_tt[0].strftime('%Y-%m-%d %H:%M:%S'), "%.2f" % kub_tt[1], "%.2f" % kb_tt[1]])
        lastObsDateTime = kub_tt[0]

    # Iterate through each timestamp
    for avg in UPPER_THEISSEN_VALUES :
        # print(avg, UPPER_THEISSEN_VALUES[avg], LOWER_THEISSEN_VALUES[avg])
        d = datetime.datetime.fromtimestamp(avg)
        if d > lastObsDateTime :
            csvWriter.writerow([d.strftime('%Y-%m-%d %H:%M:%S'), "%.2f" % KELANI_UPPER_BASIN_VALUES[avg], "%.2f" % LOWER_THEISSEN_VALUES[avg]])

except ValueError:
    raise ValueError("Incorrect data format, should be YYYY-MM-DD")
except Exception as e :
    traceback.print_exc()
finally:
    print('Completed ', RF_DIR_PATH, ' to ', RAIN_CSV_FILE_PATH)
