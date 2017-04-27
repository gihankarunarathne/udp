#!/usr/bin/python3

import os, json, subprocess, datetime, sys
from os import curdir
from os.path import join as pjoin
from sys import executable
from subprocess import Popen

from FLO2DWATERLEVEL import getWaterLevelGrid
from FLO2DWATERLEVEL import getGridBoudary
from FLO2DWATERLEVEL import getCellGrid
from FLO2DWATERLEVEL import getEsriGrid

try :
    CONFIG = json.loads(open('CONFIG.json').read())

    CWD = os.getcwd()
    BASE_OUT_FILE = 'BASE.OUT'
    WATER_LEVEL_FILE = 'water_level.asc'
    WATER_LEVEL_DIR = 'water_level'
    OUTPUT_DIR = 'OUTPUT'
    if 'BASE_OUT_FILE' in CONFIG :
        BASE_OUT_FILE = CONFIG['BASE_OUT_FILE']
    if 'WATER_LEVEL_FILE' in CONFIG :
        WATER_LEVEL_FILE = CONFIG['WATER_LEVEL_FILE']
    if 'OUTPUT_DIR' in CONFIG :
        OUTPUT_DIR = CONFIG['OUTPUT_DIR']

    # Default run for current day
    now = datetime.datetime.now()
    if len(sys.argv) > 1 : # Or taken from first arg for the program
        now = datetime.datetime.strptime(sys.argv[1], '%Y-%m-%d')
    date = now.strftime("%Y-%m-%d")
    print('Extract Result of FLO2D on', date)

    appDir = pjoin(CWD, date + '_Kelani')
    OUTPUT_DIR_PATH = pjoin(CWD, 'OUTPUT')
    BASE_OUT_FILE_PATH = pjoin(appDir, BASE_OUT_FILE)
    WATER_LEVEL_DIR_PATH = pjoin(OUTPUT_DIR_PATH, "%s-%s" % (WATER_LEVEL_DIR, date))

    # Create OUTPUT Directory
    if not os.path.exists(OUTPUT_DIR_PATH):
        os.makedirs(OUTPUT_DIR_PATH)

    bufsize = 65536
    with open(BASE_OUT_FILE_PATH) as infile: 
        i=0
        isWaterLevelLines = False
        waterLevelLines = []
        while True:
            lines = infile.readlines(bufsize)
            i += 1
            if i > 2 :
                break
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
                    fileModelTime = datetime.datetime.strptime(date, '%Y-%m-%d')
                    fileModelTime = fileModelTime + datetime.timedelta(hours=ModelTime)
                    dateAndTime = fileModelTime.strftime("%Y-%m-%d_%H-%M-%S")
                    # Create files
                    fileName = WATER_LEVEL_FILE.split('.', 1)
                    fileName = "%s-%s.%s" % (fileName[0], dateAndTime, fileName[1])
                    WATER_LEVEL_FILE_PATH = pjoin(WATER_LEVEL_DIR_PATH, fileName)
                    file = open(WATER_LEVEL_FILE_PATH, 'w')
                    file.writelines(EsriGrid)

                    isWaterLevelLines = False
                    # for l in waterLevelLines :
                        # print(l)
                    waterLevelLines = []

                if isWaterLevelLines :
                    waterLevelLines.append(line)

except Exception as e :
    traceback.print_exc()
finally:
    file.close()
    print('Completed processing', BASE_OUT_FILE_PATH, ' to ', WATER_LEVEL_FILE)