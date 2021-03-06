#!/usr/bin/python3

import collections
import csv
import datetime
import getopt
import json
import os
import re
import sys
import traceback

DSSDateTime = collections.namedtuple('DSSDateTime', ['dateTime', 'date', 'time'])


def usage():
    usage_text = """
Usage: ./Update_HECHMS.py [-d date] [-h -i] [-s sInterval] [-c cInterval] 

-h  --help          Show usage
-d  --date          Model State Date in YYYY-MM. Default is current date.
-t  --time          Model State Time in HH:MM:SS. Default is current time.
    --start-date    Start date of timeseries which need to run the forecast in YYYY-MM-DD format. Default is same as -d(date).
    --start-time    Start time of timeseries which need to run the forecast in HH:MM:SS format. Default is same as -t(date).
-i  --init          Create a State while running the HEC-HMS model
-s  --sInterval     (State Interval in minutes) Time period that state should create after start time
-c  --cInterval     (Control Interval in minutes) Time period that HEC-HMS model should run
-T  --tag           Tag to differential simultaneous Forecast Runs E.g. wrf1, wrf2 ...
    --hec-hms-model-dir Path of HEC_HMS_MODEL_DIR directory. 
                        Otherwise using the `HEC_HMS_MODEL_DIR` from CONFIG.json
"""
    print(usage_text)


def get_dss_date_time(date_time):
    # Removed DSS formatting with HEC-HMS upgrading from 3.5 to 4.1
    my_date = date_time.strftime('%d %B %Y')
    my_time = date_time.strftime('%H:%M')

    return DSSDateTime(
        dateTime=my_date + ' ' + my_time,
        date=my_date,
        time=my_time
    )


try:
    CONFIG = json.loads(open('CONFIG.json').read())
    # print('Config :: ', CONFIG)

    NUM_METADATA_LINES = 3
    HEC_HMS_MODEL_DIR = './2008_2_Events'
    HEC_HMS_CONTROL = './2008_2_Events/Control_1.control'
    HEC_HMS_RUN = './2008_2_Events/2008_2_Events.run'
    HEC_HMS_GAGE = './2008_2_Events/2008_2_Events.gage'
    RAIN_CSV_FILE = 'DailyRain.csv'
    TIME_INTERVAL = 60  # In minutes
    OUTPUT_DIR = './OUTPUT'
    STATE_INTERVAL = 1 * 24 * 60  # In minutes (1 day)
    CONTROL_INTERVAL = 8 * 24 * 60  # In minutes (8 day)

    if 'HEC_HMS_MODEL_DIR' in CONFIG :
        HEC_HMS_MODEL_DIR = CONFIG['HEC_HMS_MODEL_DIR']
    if 'HEC_HMS_CONTROL' in CONFIG :
        HEC_HMS_CONTROL = CONFIG['HEC_HMS_CONTROL']
    if 'HEC_HMS_RUN' in CONFIG :
        HEC_HMS_RUN = CONFIG['HEC_HMS_RUN']
    if 'HEC_HMS_GAGE' in CONFIG :
        HEC_HMS_GAGE = CONFIG['HEC_HMS_GAGE']
    if 'RAIN_CSV_FILE' in CONFIG :
        RAIN_CSV_FILE = CONFIG['RAIN_CSV_FILE']
    if 'TIME_INTERVAL' in CONFIG :
        TIME_INTERVAL = CONFIG['TIME_INTERVAL']
    if 'OUTPUT_DIR' in CONFIG :
            OUTPUT_DIR = CONFIG['OUTPUT_DIR']

    date = ''
    time = ''
    startDateTS = ''
    startTimeTS = ''
    initState = False
    tag = ''

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hd:t:is:c:T:", [
            "help", "date=", "time=", "start-date=", "start-time=", "backDays=", "init", "sInterval=", "cInterval=", "tag=", "hec-hms-model-dir="
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
            startDateTS = arg
        elif opt in "--start-time":
            startTimeTS = arg
        elif opt in ("-i", "--init"):
            initState = True
        elif opt in ("-s", "--sInterval"):
            STATE_INTERVAL = int(arg)
        elif opt in ("-c", "--cInterval"):
            CONTROL_INTERVAL = int(arg)
        elif opt in ("-T", "--tag"):
            tag = arg
        elif opt in "--hec-hms-model-dir":
            HEC_HMS_MODEL_DIR = arg

    # Replace CONFIG.json variables
    if re.match('^\$\{(HEC_HMS_MODEL_DIR)\}', HEC_HMS_CONTROL):
        HEC_HMS_CONTROL = re.sub('^\$\{(HEC_HMS_MODEL_DIR)\}', '', HEC_HMS_CONTROL).strip("/\\")
        HEC_HMS_CONTROL = os.path.join(HEC_HMS_MODEL_DIR, HEC_HMS_CONTROL)
        print('Set HEC_HMS_CONTROL=', HEC_HMS_CONTROL)

    if re.match('^\$\{(HEC_HMS_MODEL_DIR)\}', HEC_HMS_RUN):
        HEC_HMS_RUN = re.sub('^\$\{(HEC_HMS_MODEL_DIR)\}', '', HEC_HMS_RUN).strip("/\\")
        HEC_HMS_RUN = os.path.join(HEC_HMS_MODEL_DIR, HEC_HMS_RUN)
        print('Set HEC_HMS_RUN=', HEC_HMS_RUN)

    if re.match('^\$\{(HEC_HMS_MODEL_DIR)\}', HEC_HMS_GAGE):
        HEC_HMS_GAGE = re.sub('^\$\{(HEC_HMS_MODEL_DIR)\}', '', HEC_HMS_GAGE).strip("/\\")
        HEC_HMS_GAGE = os.path.join(HEC_HMS_MODEL_DIR, HEC_HMS_GAGE)
        print('Set HEC_HMS_GAGE=', HEC_HMS_GAGE)

    # Default run for current day
    modelState = datetime.datetime.now()
    if date:
        modelState = datetime.datetime.strptime(date, '%Y-%m-%d')
    date = modelState.strftime("%Y-%m-%d")
    if time:
        modelState = datetime.datetime.strptime('%s %s' % (date, time), '%Y-%m-%d %H:%M:%S')
    time = modelState.strftime("%H:%M:%S")

    startDateTimeTS = datetime.datetime.now()
    if startDateTS:
        startDateTimeTS = datetime.datetime.strptime(startDateTS, '%Y-%m-%d')
    else:
        startDateTimeTS = datetime.datetime.strptime(date, '%Y-%m-%d')
    startDateTS = startDateTimeTS.strftime("%Y-%m-%d")

    if startTimeTS:
        startDateTimeTS = datetime.datetime.strptime('%s %s' % (startDateTS, startTimeTS), '%Y-%m-%d %H:%M:%S')
    startTimeTS = startDateTimeTS.strftime("%H:%M:%S")

    print('Update_HECHMS startTime:', datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ', initState:', initState)
    print(' Update_HECHMS run for', date, '@', time, tag)
    print(' With Custom Time Series starting', startDateTS, '@', startTimeTS)
    print('Control Interval:', CONTROL_INTERVAL/60, 'hours')
    # Extract Start and End times
    fileName = RAIN_CSV_FILE.rsplit('.', 1)
    fileName = '{name}-{date}{tag}.{extention}'.format(name=fileName[0], date=date, tag='.'+tag if tag else '', extention=fileName[1])
    RAIN_CSV_FILE_PATH = os.path.join(OUTPUT_DIR, fileName)
    csvReader = csv.reader(open(RAIN_CSV_FILE_PATH, 'r'), delimiter=',', quotechar='|')
    csvList = list(csvReader)

    print(csvList[NUM_METADATA_LINES][0])
    print(csvList[-1][0])
    startDateTime = datetime.datetime.strptime(csvList[NUM_METADATA_LINES][0], '%Y-%m-%d %H:%M:%S')
    endDateTime = datetime.datetime.strptime(csvList[-1][0], '%Y-%m-%d %H:%M:%S')

    startDateTimeDSS = get_dss_date_time(startDateTime)
    endDateTimeDSS = get_dss_date_time(endDateTime)
    startDate = startDateTimeDSS.date
    startTime = startDateTimeDSS.time
    endDate = endDateTimeDSS.date
    endTime = endDateTimeDSS.time

    # TODO : Increase Control Interval with gap between startDateTimeTS and modelState
    controlEndDateTime = startDateTime + datetime.timedelta(minutes=CONTROL_INTERVAL)
    controlEndDateTimeDSS = get_dss_date_time(controlEndDateTime)
    controlEndDate = controlEndDateTimeDSS.date
    controlEndTime = controlEndDateTimeDSS.time

    #############################################
    # Update Control file                       #
    #############################################
    controlFile = open(HEC_HMS_CONTROL, 'r')
    controlData = controlFile.readlines()
    controlFile.close()

    controlFile = open(HEC_HMS_CONTROL, 'w')
    for line in controlData:
        if 'Start Date:' in line:
            s = line[:line.rfind('Start Date:')+11]
            s += ' ' + startDate
            controlFile.write(s + '\n')
        elif 'Start Time:' in line:
            s = line[:line.rfind('Start Time:')+11]
            s += ' ' + startTime
            controlFile.write(s + '\n')
        elif 'End Date:' in line:
            s = line[:line.rfind('End Date:')+9]
            s += ' ' + controlEndDate
            controlFile.write(s + '\n')
        elif 'End Time:' in line:
            s = line[:line.rfind('End Time:')+9]
            s += ' ' + controlEndTime
            controlFile.write(s + '\n')
        elif 'Time Interval:' in line:
            s = line[:line.rfind('Time Interval:')+14]
            s += ' ' + str(TIME_INTERVAL)
            controlFile.write(s + '\n')
        else:
            controlFile.write(line)

    #############################################
    # Update Run file                           #
    #############################################
    runFile = open(HEC_HMS_RUN, 'r')
    runData = runFile.readlines()
    runFile.close()

    runFile = open(HEC_HMS_RUN, 'w')
    for line in runData:
        if 'Control:' in line:
            runFile.write(line)
            indent = line[:line.rfind('Control:')]

            # TODO: Handle for Hour mode
            saveStateDateTime = startDateTime + datetime.timedelta(minutes=STATE_INTERVAL)
            saveStateDateTimeDSS = get_dss_date_time(saveStateDateTime)
            startStateDateTime = startDateTime - datetime.timedelta(minutes=STATE_INTERVAL)
            line1 = indent + 'Save State Name: State_' + startDateTime.strftime('%Y_%m_%d') + '_To_' + saveStateDateTime.strftime('%Y_%m_%d')
            line2 = indent + 'Save State Date: ' + saveStateDateTimeDSS.date
            line3 = indent + 'Save State Time: ' + saveStateDateTimeDSS.time
            runFile.write(line1 + '\n'); runFile.write(line2 + '\n'); runFile.write(line3 + '\n')

            if not initState:
                line4 = indent + 'Start State Name: State_' + startStateDateTime.strftime('%Y_%m_%d') + '_To_' + startDateTime.strftime('%Y_%m_%d')
                runFile.write(line4 + '\n')

        # Skip Writing these lines
        elif 'Save State At End of Run:' in line:
            continue
        elif 'Save State Name:' in line:
            continue
        elif 'Save State Date:' in line:
            continue
        elif 'Save State Time:' in line:
            continue
        elif 'Start State Name:' in line:
            continue
        else :
            runFile.write(line)

    #############################################
    # Update Gage file                          #
    #############################################
    gageFile = open(HEC_HMS_GAGE, 'r')
    gageData = gageFile.readlines()
    gageFile.close()

    gageFile = open(HEC_HMS_GAGE, 'w')
    for line in gageData:
        if 'Start Time:' in line:
            s = line[:line.rfind('Start Time:')+11]
            s += ' ' + startDate + ', ' + startTime
            gageFile.write(s + '\n')
        elif 'End Time:' in line:
            s = line[:line.rfind('End Time:')+9]
            s += ' ' + endDate + ', ' + endTime
            gageFile.write(s + '\n')
        else:
            gageFile.write(line)


except Exception as e:
    traceback.print_exc()
    print(e)
finally:
    controlFile.close()
    print('Updated HEC-HMS Control file ')
