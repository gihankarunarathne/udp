from dbadapter import mysqladapter
import sys, traceback, csv, json, datetime, getopt

def usage() :
    usageText = """
Usage: ./CSVTODAT.py [-d YYYY-MM-DD] [-h]

-h  --help          Show usage
-d  --date          Date in YYYY-MM-DD. Default is current date.
-f  --force         Force insert timeseries. If timeseries exists, delete existing data and replace with new data.
"""
    print(usageText)

try :
    CONFIG = json.loads(open('CONFIG.json').read())
    # print('Config :: ', CONFIG)

    DISCHARGE_NUM_METADATA_LINES = 2
    DISCHARGE_CSV_FILE = 'DailyDischarge.csv'
    OUTPUT_DIR = './OUTPUT'

    if 'DISCHARGE_CSV_FILE' in CONFIG :
        DISCHARGE_CSV_FILE = CONFIG['DISCHARGE_CSV_FILE']
    if 'OUTPUT_DIR' in CONFIG :
        OUTPUT_DIR = CONFIG['OUTPUT_DIR']

    date = ''
    forceInsert = False
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hd:f", ["help", "date=", "force"])
    except getopt.GetoptError:          
        usage()                        
        sys.exit(2)                     
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()                     
            sys.exit()           
        elif opt in ("-d", "--date"):
            date = arg
        elif opt in ("-f", "--force"):
            forceInsert = True

    # Default run for current day
    now = datetime.datetime.now()
    if date :
        now = datetime.datetime.strptime(date, '%Y-%m-%d')
    date = now.strftime("%Y-%m-%d")

    print('CSVTODAT startTime:', datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
except Exception as e :
    traceback.print_exc()

def storeDischarge():
    fileName = DISCHARGE_CSV_FILE.split('.', 1)
    fileName = "%s-%s.%s" % (fileName[0], date, fileName[1])
    DISCHARGE_CSV_FILE_PATH = "%s/%s" % (OUTPUT_DIR, fileName)
    csvReader = csv.reader(open(DISCHARGE_CSV_FILE_PATH, 'r'), delimiter=',', quotechar='|')
    timeseries = list(csvReader)[DISCHARGE_NUM_METADATA_LINES:]

    print('Start Date :', timeseries[0][0])
    print('End Date :', timeseries[-1][0])
    startDateTime = datetime.datetime.strptime(timeseries[0][0], '%Y:%m:%d %H:%M:%S')
    endDateTime = datetime.datetime.strptime(timeseries[-1][0], '%Y:%m:%d %H:%M:%S')

    adapter = mysqladapter()

    metaData = {
        'station': 'Hanwella',
        'variable': 'Discharge',
        'unit': 'm3',
        'rate': 1,
        'type': 'Forecast',
        'source': 'HEC-HMS',
        'name': 'HEC-HMS %s' % (date),
        'start_date': startDateTime.strftime("%Y-%m-%d %H:%M:%S"),
        'end_date': endDateTime.strftime("%Y-%m-%d %H:%M:%S")
    }
    eventId = adapter.getEventId(metaData)
    if eventId is None :
        print('eventId is None. Creating a New.')
        eventId = adapter.createEventId(metaData)
        print('HASH SHA256 : ', eventId)
        for l in timeseries[:5] :
            print(l)
        rowCount = adapter.insertTimeseries(eventId, timeseries)
        print('%s rows inserted.' % rowCount)
    else:
        print('HASH SHA256 : ', eventId)
        if forceInsert :
            deleteCount = adapter.deleteTimeseries(eventId)
            print('%s rows deleted.' % deleteCount)
            for l in timeseries[:5] :
                print(l)
            rowCount = adapter.insertTimeseries(eventId, timeseries)
            print('%s rows inserted.' % rowCount)
        else :
            print('Timeseries already exists. User -f arg to override existing timeseries.')

storeDischarge()