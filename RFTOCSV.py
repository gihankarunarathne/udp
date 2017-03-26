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
    print('Config :: ', CONFIG)
    CSV_FILE_PATH = 'DailyRainTest.csv'
    RF_DIR_PATH = './OUTPUT/RF/'
    if 'CSV_FILE_PATH' in CONFIG :
        CSV_FILE_PATH = CONFIG['CSV_FILE_PATH']
    if 'RF_DIR_PATH' in CONFIG :
        RF_DIR_PATH = CONFIG['RF_DIR_PATH']

    UPPER_CATCHMENT_WEIGHTS = {
        'Attanagalla'   : 1/7, # 1
        'Daraniyagala'  : 1/7, # 2
        'Glencourse'    : 1/7, # 3
        'Hanwella'      : 1/7, # 4
        'Holombuwa'     : 1/7, # 5
        'Kitulgala'     : 1/7, # 6
        'Norwood'       : 1/7  # 7
    }
    UPPER_CATCHMENTS = UPPER_CATCHMENT_WEIGHTS.keys()

    # now = datetime.datetime.now()
    now = datetime.datetime(2017, 3, 22)
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
    csvWriter = csv.writer(open(CSV_FILE_PATH, 'w'), delimiter=',', quotechar='|')
    for avg in THEISSEN_VALUES :
        # print(avg, THEISSEN_VALUES[avg])
        d = datetime.datetime.fromtimestamp(avg)
        csvWriter.writerow([d.strftime('%Y-%m-%d %H:%M:%S'), "%.2f" % THEISSEN_VALUES[avg]])

except Exception as e :
    traceback.print_exc()
finally:
    print('Completed ', RF_DIR_PATH, ' to ', CSV_FILE_PATH)