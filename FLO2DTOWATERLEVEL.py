#!/usr/bin/python3

import os, json, subprocess, datetime, sys, csv, traceback, getopt
from os import curdir
from os.path import join as pjoin
from sys import executable
from subprocess import Popen

def usage() :
    usageText = """
Usage: ./CSVTODAT.py [-d YYYY-MM-DD] [-t HH:MM:SS] [-h]

-h  --help          Show usage
-d  --date          Date in YYYY-MM-DD. Default is current date.
-t  --time          Time in HH:MM:SS. Default is current time.
-p  --path          FLO2D model path which include HYCHAN.OUT
"""
    print(usageText)

def isfloat(value):
  try:
    float(value)
    return True
  except ValueError:
    return False

try :
    CONFIG = json.loads(open('CONFIG.json').read())

    CWD = os.getcwd()
    HYCHAN_OUT_FILE = 'HYCHAN.OUT'
    WATER_LEVEL_FILE = 'water_level.txt'
    WATER_LEVEL_DIR = 'water_level'
    OUTPUT_DIR = 'OUTPUT'
    if 'HYCHAN_OUT_FILE' in CONFIG :
        HYCHAN_OUT_FILE = CONFIG['HYCHAN_OUT_FILE']
    if 'WATER_LEVEL_FILE' in CONFIG :
        WATER_LEVEL_FILE = CONFIG['WATER_LEVEL_FILE']
    if 'OUTPUT_DIR' in CONFIG :
        OUTPUT_DIR = CONFIG['OUTPUT_DIR']

    CELL_MAP = {
        3627 : "Ambathale",
        3626 : "Madiwela Out",
        2438 : "Salalihini Out",
        2439 : "Salalihini Out 2",
        1365 : "Kittampahuwa Bridge",
        1102 : "Kittampahuwa Out",
        1103 : "Kittampahuwa Out 2",
        645  : "N Street",
        720  : "N Street 2",
        713  : "Kolonnawa CNL 1",
        1089 : "Kolonnawa CNL 2",
        1458 : "Kolonnawa CNL 3",
        1664 : "Kolonnawa CNL 4",
        1879 : "Parliament Lake Out",
        2308 : "Parliament Lake",
        2305 : "Parliament Lake 2",
        2712 : "Parliament Upstream",
        2516 : "Ahangama",
        4327 : "Madiwela US",
        1000 : "Heen Ela",
        621  : "Torington",
        912  : "Wellawatta 1",
        763  : "Wellawatta 2",
        195  : "Wellawatta 3",
        470  : "Dehiwala 1",
        238  : "Dehiwala 2",
    }
    ELEMENT_NUMBERS = CELL_MAP.keys()
    SERIES_LENGTH = 0
    MISSING_VALUE = -999

    date = ''
    time = ''
    path = ''
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hd:t:p:", ["help", "date=", "time=", "path="])
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
        elif opt in ("-p", "--path"):
            path = arg

    # Default run for current day
    now = datetime.datetime.now()
    if date :
        now = datetime.datetime.strptime(date, '%Y-%m-%d')
    date = now.strftime("%Y-%m-%d")
    if time :
        now = datetime.datetime.strptime('%s %s' % (date, time), '%Y-%m-%d %H:%M:%S')
    time = now.strftime("%H:%M:%S")

    print('Extract Water Level Result of FLO2D on', date, '@', time)

    appDir = pjoin(CWD, date + '_Kelani')
    if path :
        appDir = pjoin(CWD, path)

    OUTPUT_DIR_PATH = pjoin(CWD, 'OUTPUT')
    HYCHAN_OUT_FILE_PATH = pjoin(appDir, HYCHAN_OUT_FILE)
    WATER_LEVEL_DIR_PATH = pjoin(OUTPUT_DIR_PATH, "%s-%s" % (WATER_LEVEL_DIR, date))

    # Check BASE.OUT file exists
    if not os.path.exists(HYCHAN_OUT_FILE_PATH):
        print('Unable to find file : ', HYCHAN_OUT_FILE_PATH)
        sys.exit()

    # Create OUTPUT Directory
    if not os.path.exists(OUTPUT_DIR_PATH):
        os.makedirs(OUTPUT_DIR_PATH)

    # Calculate the size of time series
    bufsize = 65536
    with open(HYCHAN_OUT_FILE_PATH) as infile: 
        isWaterLevelLines = False
        isCounting = False
        countSeriesSize = 0 # HACK: When it comes to the end of file, unable to detect end of time series
        while True:
            lines = infile.readlines(bufsize)
            if not lines or SERIES_LENGTH:
                break
            for line in lines:
                if line.startswith('CHANNEL HYDROGRAPH FOR ELEMENT NO:', 5) :
                    isWaterLevelLines = True
                elif isWaterLevelLines :
                    cols = line.split()
                    if len(cols) > 0 and cols[0].replace('.','',1).isdigit() :
                        countSeriesSize += 1
                        isCounting = True
                    elif isWaterLevelLines and isCounting :
                        SERIES_LENGTH = countSeriesSize
                        break

    print('Series Length is :', SERIES_LENGTH)
    bufsize = 65536
    with open(HYCHAN_OUT_FILE_PATH) as infile: 
        isWaterLevelLines = False
        isSeriesComplete = False
        waterLevelLines = []
        seriesSize = 0 # HACK: When it comes to the end of file, unable to detect end of time series
        while True:
            lines = infile.readlines(bufsize)
            if not lines:
                break
            for line in lines:
                if line.startswith('CHANNEL HYDROGRAPH FOR ELEMENT NO:', 5) :
                    seriesSize = 0
                    elementNo = int(line.split()[5])

                    if elementNo in ELEMENT_NUMBERS :
                        isWaterLevelLines = True
                        waterLevelLines.append(line)
                    else :
                        isWaterLevelLines = False

                elif isWaterLevelLines :
                    cols = line.split()
                    if len(cols) > 0 and isfloat(cols[0]) :
                        seriesSize += 1
                        waterLevelLines.append(line)

                        if seriesSize == SERIES_LENGTH :
                            isSeriesComplete = True

                if isSeriesComplete :
                    baseTime = datetime.datetime.strptime(date, '%Y-%m-%d')
                    timeseries = []
                    elementNo = int(waterLevelLines[0].split()[5])
                    print('Extracted Cell No', elementNo, CELL_MAP[elementNo])
                    for ts in waterLevelLines[1:] :
                        v = ts.split()
                        if len(v) < 1 :
                            continue
                        # Get flood level (Elevation)
                        value = v[1]
                        # Get flood depth (Depth)
                        # value = v[2]
                        if not isfloat(value) :
                            value = MISSING_VALUE
                            continue # If value is not present, skip
                        if value == 'NaN' :
                            continue # If value is NaN, skip
                        timeStep = float(v[0])
                        currentStepTime = baseTime + datetime.timedelta(hours=timeStep)
                        dateAndTime = currentStepTime.strftime("%Y-%m-%d %H:%M:%S")
                        timeseries.append([dateAndTime, value])

                    # Create Directory
                    if not os.path.exists(WATER_LEVEL_DIR_PATH):
                        os.makedirs(WATER_LEVEL_DIR_PATH)
                    # Get Time stamp Ref:http://stackoverflow.com/a/13685221/1461060
                    ModelTime = float(waterLevelLines[1].split()[3])
                    fileModelTime = datetime.datetime.strptime(date, '%Y-%m-%d')
                    fileModelTime = fileModelTime + datetime.timedelta(hours=ModelTime)
                    dateAndTime = fileModelTime.strftime("%Y-%m-%d_%H-%M-%S")
                    # Create files
                    fileName = WATER_LEVEL_FILE.split('.', 1)
                    fileName = "%s-%s-%s.%s" % (fileName[0], CELL_MAP[elementNo].replace(' ', '_'), date, fileName[1])
                    WATER_LEVEL_FILE_PATH = pjoin(WATER_LEVEL_DIR_PATH, fileName)
                    csvWriter = csv.writer(open(WATER_LEVEL_FILE_PATH, 'w'), delimiter=',', quotechar='|')
                    csvWriter.writerows(timeseries)

                    isWaterLevelLines = False
                    isSeriesComplete = False
                    waterLevelLines = []


except Exception as e :
    traceback.print_exc()
finally:
    print('Completed processing', HYCHAN_OUT_FILE_PATH, ' to ', WATER_LEVEL_FILE_PATH)