#!/usr/bin/python3

import os
import glob
import csv
import json
from string import Template
import sys, traceback
import datetime
from collections import OrderedDict

try :
    CONFIG = json.loads(open('CONFIG.json').read())
    # print('Config :: ', CONFIG)
    RAIN_CSV_FILE = 'DailyRain.csv'
    RF_DIR_PATH = './OUTPUT/RF/'
    OUTPUT_DIR = './OUTPUT'
    if 'RAIN_CSV_FILE' in CONFIG :
        RAIN_CSV_FILE = CONFIG['RAIN_CSV_FILE']
    if 'RF_DIR_PATH' in CONFIG :
        RF_DIR_PATH = CONFIG['RF_DIR_PATH']
    if 'OUTPUT_DIR' in CONFIG :
        OUTPUT_DIR = CONFIG['OUTPUT_DIR']

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

    LOWER_CATCHMENT_WEIGHTS = {
        'Colombo'       :  1
    }
    LOWER_CATCHMENTS = LOWER_CATCHMENT_WEIGHTS.keys()

    # Default run for current day
    now = datetime.datetime.now()
    if len(sys.argv) > 1 : # Or taken from first arg for the program
        now = datetime.datetime.strptime(sys.argv[1], '%Y-%m-%d')
    date = now.strftime("%Y-%m-%d")

    UPPER_THEISSEN_VALUES = OrderedDict()
    for catchment in UPPER_CATCHMENTS :
        for filename in glob.glob(os.path.join(RF_DIR_PATH, catchment+date+'*.txt')):
            print('Start Operating on (Upper) ', filename)
            csvCatchment = csv.reader(open(filename, 'r'), delimiter=',', skipinitialspace=True)
            csvCatchment = list(csvCatchment)
            for row in csvCatchment :
                # print(row[0].replace('_', ' '), row[1].strip(' \t'))
                d = datetime.datetime.strptime(row[0].replace('_', ' '), '%Y-%m-%d %H:%M:%S')
                key = d.timestamp()
                if key not in UPPER_THEISSEN_VALUES :
                    UPPER_THEISSEN_VALUES[key] = 0
                UPPER_THEISSEN_VALUES[key] += float(row[1].strip(' \t')) * UPPER_CATCHMENT_WEIGHTS[catchment]

    LOWER_THEISSEN_VALUES = OrderedDict()
    for lowerCatchment in LOWER_CATCHMENTS :
        for filename in glob.glob(os.path.join(RF_DIR_PATH, lowerCatchment+date+'*.txt')):
            print('Start Operating on (Lower) ', filename)
            csvCatchment = csv.reader(open(filename, 'r'), delimiter=',', skipinitialspace=True)
            csvCatchment = list(csvCatchment)
            for row in csvCatchment :
                # print(row[0].replace('_', ' '), row[1].strip(' \t'))
                d = datetime.datetime.strptime(row[0].replace('_', ' '), '%Y-%m-%d %H:%M:%S')
                key = d.timestamp()
                if key not in LOWER_THEISSEN_VALUES :
                    LOWER_THEISSEN_VALUES[key] = 0
                LOWER_THEISSEN_VALUES[key] += float(row[1].strip(' \t')) * LOWER_CATCHMENT_WEIGHTS[lowerCatchment]

    print('Finished processing files. Start Writing Theissen polygon avg in to CSV')
    # print(UPPER_THEISSEN_VALUES)
    fileName = RAIN_CSV_FILE.split('.', 1)
    fileName = "%s-%s.%s" % (fileName[0], date, fileName[1])
    RAIN_CSV_FILE_PATH = "%s/%s" % (OUTPUT_DIR, fileName)
    csvWriter = csv.writer(open(RAIN_CSV_FILE_PATH, 'w'), delimiter=',', quotechar='|')
    # Write Metadata https://publicwiki.deltares.nl/display/FEWSDOC/CSV
    csvWriter.writerow(['Location Names', 'Awissawella', 'Colombo'])
    csvWriter.writerow(['Location Ids', 'Awissawella', 'Colombo'])
    csvWriter.writerow(['Time', 'Rainfall', 'Rainfall'])

    for avg in UPPER_THEISSEN_VALUES :
        # print(avg, UPPER_THEISSEN_VALUES[avg], LOWER_THEISSEN_VALUES[avg])
        d = datetime.datetime.fromtimestamp(avg)
        csvWriter.writerow([d.strftime('%Y-%m-%d %H:%M:%S'), "%.2f" % UPPER_THEISSEN_VALUES[avg], "%.2f" % LOWER_THEISSEN_VALUES[avg]])

except ValueError:
    raise ValueError("Incorrect data format, should be YYYY-MM-DD")
except Exception as e :
    traceback.print_exc()
finally:
    print('Completed ', RF_DIR_PATH, ' to ', RAIN_CSV_FILE_PATH)