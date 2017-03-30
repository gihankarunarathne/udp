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
    if 'RAIN_CSV_FILE' in CONFIG :
        RAIN_CSV_FILE = CONFIG['RAIN_CSV_FILE']
    if 'RF_DIR_PATH' in CONFIG :
        RF_DIR_PATH = CONFIG['RF_DIR_PATH']

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

    # Default run for current day
    now = datetime.datetime.now()
    if len(sys.argv) > 1 :
        now = datetime.datetime.strptime(sys.argv[1], '%Y-%m-%d')
    date = now.strftime("%Y-%m-%d")
    THEISSEN_VALUES = OrderedDict()
    for catchment in UPPER_CATCHMENTS :
        for filename in glob.glob(os.path.join(RF_DIR_PATH, catchment+date+'*.txt')):
            print('Start Operating on ', filename)
            csvCatchment = csv.reader(open(filename, 'r'), delimiter=',', skipinitialspace=True)
            csvCatchment = list(csvCatchment)
            for row in csvCatchment :
                # print(row[0].replace('_', ' '), row[1].strip(' \t'))
                d = datetime.datetime.strptime(row[0].replace('_', ' '), '%Y-%m-%d %H:%M:%S')
                key = d.timestamp()
                if key not in THEISSEN_VALUES :
                    THEISSEN_VALUES[key] = 0
                THEISSEN_VALUES[key] += float(row[1].strip(' \t')) * UPPER_CATCHMENT_WEIGHTS[catchment]

    print('Finished processing files. Start Writing Theissen polygon avg in to CSV')
    # print(THEISSEN_VALUES)
    csvWriter = csv.writer(open(RAIN_CSV_FILE, 'w'), delimiter=',', quotechar='|')
    for avg in THEISSEN_VALUES :
        # print(avg, THEISSEN_VALUES[avg])
        d = datetime.datetime.fromtimestamp(avg)
        csvWriter.writerow([d.strftime('%Y-%m-%d %H:%M:%S'), "%.2f" % THEISSEN_VALUES[avg]])

except ValueError:
    raise ValueError("Incorrect data format, should be YYYY-MM-DD")
except Exception as e :
    traceback.print_exc()
finally:
    print('Completed ', RF_DIR_PATH, ' to ', RAIN_CSV_FILE)