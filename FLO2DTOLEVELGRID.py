#!/usr/bin/python3

import os, json, subprocess, datetime, sys, csv, traceback, getopt
from os import curdir
from os.path import join as pjoin
from sys import executable
from subprocess import Popen

from FLO2DWATERLEVEL import getWaterLevelGrid
from FLO2DWATERLEVEL import getGridBoudary
from FLO2DWATERLEVEL import getCellGrid
from FLO2DWATERLEVEL import getEsriGrid

def usage() :
    usageText = """
Usage: ./FLO2DTOLEVELGRID.py [-d YYYY-MM-DD] [-t HH:MM:SS] [-p -o -h] [-S YYYY-MM-DD] [-T HH:MM:SS]

-h  --help          Show usage
-d  --date          Date in YYYY-MM-DD. Default is current date.
-t  --time          Time in HH:MM:SS. If -d passed, then default is 00:00:00. Otherwise Default is current time.
-p  --path          FLO2D model path which include HYCHAN.OUT
-o  --out           Suffix for 'water_level-<SUFFIX>' and 'water_level_grid-<SUFFIX>' output directories.
                    Default is 'water_level-<YYYY-MM-DD>' and 'water_level_grid-<YYYY-MM-DD>' same as -d option value.
-S  --start_date    Base Date of FLO2D model output in YYYY-MM-DD format. Default is same as -d option value.
-T  --start_time    Base Time of FLO2D model output in HH:MM:SS format. Default is set to 00:00:00
"""
    print(usageText)

try :
    CONFIG = json.loads(open('CONFIG.json').read())

    CWD = os.getcwd()
    BASE_OUT_FILE = 'BASE.OUT'
    WATER_LEVEL_FILE = 'water_level_grid.asc'
    WATER_LEVEL_DIR = 'water_level_grid'
    OUTPUT_DIR = 'OUTPUT'
    if 'BASE_OUT_FILE' in CONFIG :
        BASE_OUT_FILE = CONFIG['BASE_OUT_FILE']
    if 'WATER_LEVEL_FILE' in CONFIG :
        WATER_LEVEL_FILE = CONFIG['WATER_LEVEL_FILE']
    if 'OUTPUT_DIR' in CONFIG :
        OUTPUT_DIR = CONFIG['OUTPUT_DIR']

    date = ''
    time = ''
    path = ''
    output_suffix = ''
    start_date = ''
    start_time = ''

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hd:t:p:o:S:T:", ["help", "date=", "time=", "path=", "out=", "start_date=", "start_time="])
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
            path = arg.strip()
        elif opt in ("-o", "--out"):
            output_suffix = arg.strip()
        elif opt in ("-S", "--start_date"):
            start_date = arg.strip()
        elif opt in ("-T", "--start_time"):
            start_time = arg.strip()

    # Default run for current day
    now = datetime.datetime.now()
    if date :
        now = datetime.datetime.strptime(date, '%Y-%m-%d')
    date = now.strftime("%Y-%m-%d")
    if time :
        now = datetime.datetime.strptime('%s %s' % (date, time), '%Y-%m-%d %H:%M:%S')
    time = now.strftime("%H:%M:%S")

    if start_date :
        start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        start_date = start_date.strftime("%Y-%m-%d")
    elif :
        start_date = date

    if start_time :
        start_time = datetime.datetime.strptime('%s %s' % (start_date, start_time), '%Y-%m-%d %H:%M:%S')
        start_time = start_time.strftime("%H:%M:%S")
    elif :
        start_time = datetime.datetime.strptime(start_date, '%Y-%m-%d') # Time is set to 00:00:00
        start_time = start_time.strftime("%H:%M:%S")

    print('Extract Water Level Grid Result of FLO2D on', date, '@', time, 'with Bast time of', start_date, '@', start_time)

    appDir = pjoin(CWD, date + '_Kelani')
    if path :
        appDir = pjoin(CWD, path)

    OUTPUT_DIR_PATH = pjoin(CWD, OUTPUT_DIR)
    BASE_OUT_FILE_PATH = pjoin(appDir, BASE_OUT_FILE)

    WATER_LEVEL_DIR_PATH = pjoin(OUTPUT_DIR_PATH, "%s-%s" % (WATER_LEVEL_DIR, date))
    if output_suffix :
            WATER_LEVEL_DIR_PATH = pjoin(OUTPUT_DIR_PATH, "%s-%s" % (WATER_LEVEL_DIR, output_suffix))

    print('Processing FLO2D model on', appDir)

    # Check BASE.OUT file exists
    if not os.path.exists(BASE_OUT_FILE_PATH):
        print('Unable to find file : ', BASE_OUT_FILE_PATH)
        sys.exit()

    # Create OUTPUT Directory
    if not os.path.exists(OUTPUT_DIR_PATH):
        os.makedirs(OUTPUT_DIR_PATH)

    bufsize = 65536
    with open(BASE_OUT_FILE_PATH) as infile: 
        isWaterLevelLines = False
        waterLevelLines = []
        while True:
            lines = infile.readlines(bufsize)

            if not lines:
                break
            for line in lines:
                if line.startswith('MODEL TIME =', 5) :
                    isWaterLevelLines = True
                elif isWaterLevelLines and line.startswith('***CHANNEL RESULTS***', 17) :
                    waterLevels = getWaterLevelGrid(waterLevelLines)
                    boundary    = getGridBoudary()
                    CellGrid    = getCellGrid(boundary)
                    EsriGrid    = getEsriGrid(waterLevels, boundary, CellGrid)

                    # Create Directory
                    if not os.path.exists(WATER_LEVEL_DIR_PATH):
                        os.makedirs(WATER_LEVEL_DIR_PATH)
                    # Get Time stamp Ref:http://stackoverflow.com/a/13685221/1461060
                    ModelTime = float(waterLevelLines[0].split()[3])
                    fileModelTime = datetime.datetime.strptime('%s %s' % (start_date, start_time), '%Y-%m-%d %H:%M:%S')
                    fileModelTime = fileModelTime + datetime.timedelta(hours=ModelTime)
                    dateAndTime = fileModelTime.strftime("%Y-%m-%d_%H-%M-%S")
                    # Create files
                    fileName = WATER_LEVEL_FILE.split('.', 1)
                    fileName = "%s-%s.%s" % (fileName[0], dateAndTime, fileName[1])
                    WATER_LEVEL_FILE_PATH = pjoin(WATER_LEVEL_DIR_PATH, fileName)
                    file = open(WATER_LEVEL_FILE_PATH, 'w')
                    file.writelines(EsriGrid)
                    file.close()
                    print('Write to :', fileName)

                    isWaterLevelLines = False
                    # for l in waterLevelLines :
                        # print(l)
                    waterLevelLines = []

                if isWaterLevelLines :
                    waterLevelLines.append(line)

except Exception as e :
    traceback.print_exc()
finally:
    print('Completed processing', BASE_OUT_FILE_PATH, ' to ', WATER_LEVEL_FILE)