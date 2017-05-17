#!/usr/bin/python3

from string import Template
import sys, traceback, csv, json, datetime, getopt

def usage() :
    usageText = """
Usage: ./CSVTODAT.py [-d YYYY-MM-DD] [-h]

-h  --help          Show usage
-d  --date          Date in YYYY-MM-DD. Default is current date.
"""
    print(usageText)

try :
    CONFIG = json.loads(open('CONFIG.json').read())
    # print('Config :: ', CONFIG)

    CSV_NUM_METADATA_LINES = 2
    DAT_WIDTH = 12
    DISCHARGE_CSV_FILE = 'DailyDischarge.csv'
    INFLOW_DAT_FILE = './FLO2D/INFLOW.DAT'
    OUTPUT_DIR = './OUTPUT'

    if 'DISCHARGE_CSV_FILE' in CONFIG :
        DISCHARGE_CSV_FILE = CONFIG['DISCHARGE_CSV_FILE']
    if 'INFLOW_DAT_FILE' in CONFIG :
        INFLOW_DAT_FILE = CONFIG['INFLOW_DAT_FILE']
    if 'OUTPUT_DIR' in CONFIG :
        OUTPUT_DIR = CONFIG['OUTPUT_DIR']

    date = ''
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hd:", ["help", "date="])
    except getopt.GetoptError:          
        usage()                        
        sys.exit(2)                     
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()                     
            sys.exit()           
        elif opt in ("-d", "--date"):
            date = arg

    # FLO-2D parameters
    IHOURDAILY  = 0     # 0-hourly interval, 1-daily interval
    IDEPLT      = 8672
    IFC         = 'F'   # foodplain 'F' or a channel 'C'
    INOUTFC     = 0     # 0-inflow, 1-outflow
    KHIN        = 8672 # inflow nodes
    HYDCHAR     = 'H'   # Denote line of inflow hydrograph time and discharge pairs

    # Default run for current day
    now = datetime.datetime.now()
    if date :
        now = datetime.datetime.strptime(date, '%Y-%m-%d')
    date = now.strftime("%Y-%m-%d")

    print('CSVTODAT startTime:', datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    fileName = DISCHARGE_CSV_FILE.split('.', 1)
    fileName = "%s-%s.%s" % (fileName[0], date, fileName[1])
    DISCHARGE_CSV_FILE_PATH = "%s/%s" % (OUTPUT_DIR, fileName)
    csvReader = csv.reader(open(DISCHARGE_CSV_FILE_PATH, 'r'), delimiter=',', quotechar='|')
    csvList = list(csvReader)

    f = open(INFLOW_DAT_FILE, 'w')
    line1 = '{0} {1:{w}{b}}\n'.format(IHOURDAILY, IDEPLT, b='d', w=DAT_WIDTH)
    line2 = '{0} {1:{w}{b}} {2:{w}{b}}\n'.format(IFC, INOUTFC, KHIN, b='d', w=DAT_WIDTH)
    line3 = '{0} {1:{w}{b}} {2:{w}{b}}\n'.format(HYDCHAR, 0.0, 0.0, b='.1f', w=DAT_WIDTH)
    f.writelines([line1, line2, line3])

    lines = []; i = 1.0
    for value in csvList[CSV_NUM_METADATA_LINES:]:
        lines.append('{0} {1:{w}{b}} {2:{w}{b}}\n'.format(HYDCHAR, i, float(value[1]), b='.1f', w=DAT_WIDTH))
        i += 1.0

    f.writelines(lines)

except Exception as e :
    traceback.print_exc()
finally:
    f.close()
    print('Completed ', DISCHARGE_CSV_FILE_PATH, ' to ', INFLOW_DAT_FILE)