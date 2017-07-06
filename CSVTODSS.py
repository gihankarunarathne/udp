#!/usr/bin/python

# Rainfall CSV file format should follow as 
# https://publicwiki.deltares.nl/display/FEWSDOC/CSV 

import java, csv, sys, datetime
from hec.script import MessageBox
from hec.heclib.dss import HecDss
from hec.heclib.util import HecTime
from hec.io import TimeSeriesContainer

from optparse import OptionParser

sys.path.append("./simplejson-2.5.2")
import simplejson as json

try :
    try :
        print 'Jython version: ', sys.version

        CONFIG = json.loads(open('CONFIG.json').read())
        # print('Config :: ', CONFIG)

        NUM_METADATA_LINES = 3;
        DSS_INPUT_FILE = './2008_2_Events/2008_2_Events_force.dss'
        RAIN_CSV_FILE = 'DailyRain.csv'
        OUTPUT_DIR = './OUTPUT'

        if 'DSS_INPUT_FILE' in CONFIG :
            DSS_INPUT_FILE = CONFIG['DSS_INPUT_FILE']
        if 'RAIN_CSV_FILE' in CONFIG :
            RAIN_CSV_FILE = CONFIG['RAIN_CSV_FILE']
        if 'OUTPUT_DIR' in CONFIG :
            OUTPUT_DIR = CONFIG['OUTPUT_DIR']

        date = ''

        # Passing Commandline Options to Jython. Not same as getopt in python.
        # Ref: http://www.jython.org/jythonbook/en/1.0/Scripting.html#parsing-commandline-options
        # Doc : https://docs.python.org/2/library/optparse.html
        parser = OptionParser(description='Upload CSV data into HEC-HMS DSS storage')
        # ERROR: Unable to use `-d` or `-D` option with OptionParser
        parser.add_option("-t", "--date", help="Date in YYYY-MM. Default is current date.")

        (options, args) = parser.parse_args()
        print 'Commandline Options:', options

        if options.date :
            date = options.date

        # Default run for current day
        now = datetime.datetime.now()
        if date :
            now = datetime.datetime.strptime(date, '%Y-%m-%d')
        date = now.strftime("%Y-%m-%d")
        print 'Start CSVTODSS.py on ', date

        myDss = HecDss.open(DSS_INPUT_FILE)
        fileName = RAIN_CSV_FILE.split('.', 1)
        fileName = "%s-%s.%s" % (fileName[0], date, fileName[1])
        RAIN_CSV_FILE_PATH = "%s/%s" % (OUTPUT_DIR, fileName)
        csvReader = csv.reader(open(RAIN_CSV_FILE_PATH, 'r'), delimiter=',', quotechar='|')
        csvList = list(csvReader)
        
        numLocations = len(csvList[0]) - 1
        numValues = len(csvList) - NUM_METADATA_LINES # Ignore Metadata
        locationIds = csvList[1][1:]
        print 'Start reading', numLocations, csvList[0][0], ':', ', '.join(csvList[0][1:])
        print 'Period of ', numValues, 'values'
        print 'Location Ids :', locationIds

        for i in range(0, numLocations):
            print '\n>>>>>>> Start processing ', locationIds[i], '<<<<<<<<<<<<'
            precipitations = []
            for j in range(NUM_METADATA_LINES, numValues + NUM_METADATA_LINES):
                p = float(csvList[j][i+1])
                precipitations.append(p)

            print 'Precipitation of ', locationIds[i], precipitations[:10]
            tsc = TimeSeriesContainer()
            # tsc.fullName = "/BASIN/LOC/FLOW//1HOUR/OBS/"
            # tsc.fullName = '//' + locationIds[i].upper() + '/PRECIP-INC//1DAY/GAGE/'
            tsc.fullName = '//' + locationIds[i].upper() + '/PRECIP-INC//1HOUR/GAGE/'

            print 'Start time : ', csvList[NUM_METADATA_LINES][0]
            start = HecTime(csvList[NUM_METADATA_LINES][0])
            tsc.interval = 60 # in minutes
            times = []
            for value in precipitations :
              times.append(start.value())
              start.add(tsc.interval)
            tsc.times = times
            tsc.values = precipitations
            tsc.numberValues = len(precipitations)
            tsc.units = "MM"
            tsc.type = "PER-CUM"
            myDss.put(tsc)

    except Exception, e :
        MessageBox.showError(' '.join(e.args), "Python Error")
    except java.lang.Exception, e :
        MessageBox.showError(e.getMessage(), "Error")
finally :
    myDss.done()
    print '\nCompleted converting ', RAIN_CSV_FILE_PATH, ' to ', DSS_INPUT_FILE
    print 'done'