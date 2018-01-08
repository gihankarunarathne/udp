#!/usr/bin/python3

import getopt
import json
import sys
import traceback
from datetime import datetime, timedelta

from curwmysqladapter import MySQLAdapter


def usage():
    usage_text = """
Usage: ./TIDAL_TO_OUTFLOW.py [-d YYYY-MM-DD] [-h]

-h  --help          Show usage
-d  --date          Model State Date in YYYY-MM. Default is current date.
-t  --time          Model State Time in HH:MM:SS. Default is current time.
    --start-date    Start date of timeseries which need to run the forecast in YYYY-MM-DD format.
                    Default is same as -d(date).
    --start-time    Start time of timeseries which need to run the forecast in HH:MM:SS format.
                    Default is same as -t(date).
-T  --tag           Tag to differential simultaneous Forecast Runs E.g. wrf1, wrf2 ...
-f  --forceInsert   Force Insert into the database. May override existing values.
-n  --name          Name field value of the Run table in Database.
                    Use time format such as 'Cloud-1-<%H:%M:%S>' to replace with time(t).
"""
    print(usage_text)


def get_forecast_timeseries(my_adapter, my_event_id, my_opts):
    existing_timeseries = my_adapter.retrieve_timeseries([my_event_id], my_opts)
    new_timeseries = []
    if len(existing_timeseries) > 0 and len(existing_timeseries[0]['timeseries']) > 0:
        existing_timeseries = existing_timeseries[0]['timeseries']
        for ex_step in existing_timeseries:
            if ex_step[0] - ex_step[0].replace(minute=0, second=0, microsecond=0) > timedelta(minutes=30):
                new_timeseries.append(
                    [ex_step[0].replace(minute=0, second=0, microsecond=0) + timedelta(hours=1), ex_step[1]])
            else:
                new_timeseries.append(
                    [ex_step[0].replace(minute=0, second=0, microsecond=0), ex_step[1]])

    return new_timeseries


f = None
try:
    CONFIG = json.loads(open('CONFIG.json').read())
    # print('Config :: ', CONFIG)

    CSV_NUM_METADATA_LINES = 2
    DAT_WIDTH = 12
    TIDAL_FORECAST_ID = "ebcc2df39aea35de15cca81bc5f15baffd94bcebf3f169add1fd43ee1611d367"
    CONTROL_INTERVAL = 6 * 24 * 60  # In minutes (6 day)
    OUTFLOW_DAT_FILE = './FLO2D/OUTFLOW.DAT'
    OUTPUT_DIR = './OUTPUT'
    INIT_TIDAL_CONFIG = './Template/INITTIDAL.CONF'

    MYSQL_HOST = "localhost"
    MYSQL_USER = "root"
    MYSQL_DB = "curw"
    MYSQL_PASSWORD = ""

    if 'OUTFLOW_DAT_FILE' in CONFIG:
        OUTFLOW_DAT_FILE = CONFIG['OUTFLOW_DAT_FILE']
    if 'OUTPUT_DIR' in CONFIG:
        OUTPUT_DIR = CONFIG['OUTPUT_DIR']
    if 'INIT_TIDAL_CONFIG' in CONFIG:
        INIT_TIDAL_CONFIG = CONFIG['INIT_TIDAL_CONFIG']

    if 'MYSQL_HOST' in CONFIG:
        MYSQL_HOST = CONFIG['MYSQL_HOST']
    if 'MYSQL_USER' in CONFIG:
        MYSQL_USER = CONFIG['MYSQL_USER']
    if 'MYSQL_DB' in CONFIG:
        MYSQL_DB = CONFIG['MYSQL_DB']
    if 'MYSQL_PASSWORD' in CONFIG:
        MYSQL_PASSWORD = CONFIG['MYSQL_PASSWORD']

    date = ''
    time = ''
    startDate = ''
    startTime = ''
    tag = ''
    forceInsert = False
    runName = 'Cloud-1'

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hd:t:T:fn:", [
            "help", "date=", "time=", "start-date=", "start-time=", "tag=", "force", "runName="
        ])
    except getopt.GetoptError:          
        usage()                        
        sys.exit(2)                     
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit(0)
        elif opt in ("-d", "--date"):
            date = arg
        elif opt in ("-t", "--time"):
            time = arg
        elif opt in "--start-date":
            startDate = arg
        elif opt in "--start-time":
            startTime = arg
        elif opt in ("-T", "--tag"):
            tag = arg
        elif opt in ("-f", "--force"):
            forceInsert = True
        elif opt in ("-n", "--name"):
            runName = arg

    # Default run for current day
    modelState = datetime.now()
    if date:
        modelState = datetime.strptime(date, '%Y-%m-%d')
    date = modelState.strftime("%Y-%m-%d")
    if time:
        modelState = datetime.strptime('%s %s' % (date, time), '%Y-%m-%d %H:%M:%S')
    time = modelState.strftime("%H:%M:%S")

    startDateTime = datetime.now()
    if startDate:
        startDateTime = datetime.strptime(startDate, '%Y-%m-%d')
    else:
        startDateTime = datetime.strptime(date, '%Y-%m-%d')
    startDate = startDateTime.strftime("%Y-%m-%d")

    if startTime:
        startDateTime = datetime.strptime('%s %s' % (startDate, startTime), '%Y-%m-%d %H:%M:%S')
    startTime = startDateTime.strftime("%H:%M:%S")

    print('TIDAL_TO_OUTFLOW startTime:', datetime.now().strftime("%Y-%m-%d %H:%M:%S"), tag)
    print(' TIDAL_TO_OUTFLOW run for', date, '@', time, tag)
    print(' With Custom starting', startDate, '@', startTime, ' run name:', runName)

    # Get Observed Data
    adapter = MySQLAdapter(host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD, db=MYSQL_DB)
    opts = {
        'from': (startDateTime - timedelta(minutes=0)).strftime("%Y-%m-%d %H:%M:%S"),
        'to': (startDateTime + timedelta(minutes=CONTROL_INTERVAL)).strftime("%Y-%m-%d %H:%M:%S"),
    }
    tidal_timeseries = get_forecast_timeseries(adapter, TIDAL_FORECAST_ID, opts)
    if len(tidal_timeseries) > 0:
        print('tidal_timeseries::', len(tidal_timeseries), tidal_timeseries[0], tidal_timeseries[-1])
    else:
        print('No data found for tidal timeseries: ', tidal_timeseries)
        sys.exit(1)

    fileName = OUTFLOW_DAT_FILE.rsplit('.', 1)
    OUTFLOW_DAT_FILE_PATH = '{name}{tag}.{extension}'.\
        format(name=fileName[0], tag='.' + tag if tag else '', extension=fileName[1])
    print('Open FLO2D OUTFLOW ::', OUTFLOW_DAT_FILE_PATH)
    f = open(OUTFLOW_DAT_FILE_PATH, 'w')
    lines = []

    print('Reading INIT TIDAL CONF...')
    with open(INIT_TIDAL_CONFIG) as initTidalConfFile:
        initTidalLevels = initTidalConfFile.readlines()
        for initTidalLevel in initTidalLevels:
            if len(initTidalLevel.split()):  # Check if not empty line
                lines.append(initTidalLevel)
                if initTidalLevel[0] == 'N':
                    lines.append('{0} {1:{w}} {2:{w}}\n'.format('S', 0, 0, w=DAT_WIDTH))
                    base_date_time = startDateTime.replace(minute=0, second=0, microsecond=0)
                    for step in tidal_timeseries:
                        hours_so_far = (step[0] - base_date_time)
                        hours_so_far = 24 * hours_so_far.days + hours_so_far.seconds / (60 * 60)
                        lines.append('{0} {1:{w}} {2:{w}{b}}\n'
                                     .format('S', int(hours_so_far), float(step[1]), b='.2f', w=DAT_WIDTH))

    f.writelines(lines)
    print('Finished writing OUTFLOW.DAT')

except Exception as e:
    print(e)
    traceback.print_exc()
finally:
    if f:
        f.close()
