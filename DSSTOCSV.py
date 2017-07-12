#!/usr/bin/python

import java, csv, sys, datetime, os, re

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

        NUM_METADATA_LINES = 2;
        HEC_HMS_MODEL_DIR = './2008_2_Events'
        DSS_OUTPUT_FILE = './2008_2_Events/2008_2_Events.dss'
        DISCHARGE_CSV_FILE = 'DailyDischarge.csv'
        OUTPUT_DIR = './OUTPUT'

        if 'HEC_HMS_MODEL_DIR' in CONFIG :
            HEC_HMS_MODEL_DIR = CONFIG['HEC_HMS_MODEL_DIR']
        if 'DSS_OUTPUT_FILE' in CONFIG :
            DSS_OUTPUT_FILE = CONFIG['DSS_OUTPUT_FILE']
        if 'DISCHARGE_CSV_FILE' in CONFIG :
            DISCHARGE_CSV_FILE = CONFIG['DISCHARGE_CSV_FILE']
        if 'OUTPUT_DIR' in CONFIG :
            OUTPUT_DIR = CONFIG['OUTPUT_DIR']

        date = ''
        tag = ''

        # Passing Commandline Options to Jython. Not same as getopt in python.
        # Ref: http://www.jython.org/jythonbook/en/1.0/Scripting.html#parsing-commandline-options
        # Doc : https://docs.python.org/2/library/optparse.html
        parser = OptionParser(description='Upload CSV data into HEC-HMS DSS storage')
        # ERROR: Unable to use `-d` or `-D` option with OptionParser
        parser.add_option("-t", "--date", help="Date in YYYY-MM. Default is current date.")
        parser.add_option("-T", "--tag", help="Tag to differential simultaneous Forecast Runs E.g. wrf1, wrf2 ...")

        (options, args) = parser.parse_args()
        print 'Commandline Options:', options

        if options.date :
            date = options.date
        if options.tag :
            tag = options.tag

        # Replace CONFIG.json variables
        if re.match('^\$\{(HEC_HMS_MODEL_DIR)\}', DSS_OUTPUT_FILE) :
            DSS_OUTPUT_FILE = re.sub('^\$\{(HEC_HMS_MODEL_DIR)\}', '', DSS_OUTPUT_FILE).strip("/\\")
            DSS_OUTPUT_FILE = os.path.join(HEC_HMS_MODEL_DIR, DSS_OUTPUT_FILE)
            print '"Set DSS_OUTPUT_FILE=', DSS_OUTPUT_FILE

        # Default run for current day
        now = datetime.datetime.now()
        if date :
            now = datetime.datetime.strptime(date, '%Y-%m-%d')
        date = now.strftime("%Y-%m-%d")

        myDss = HecDss.open(DSS_OUTPUT_FILE)
        fileName = DISCHARGE_CSV_FILE.rsplit('.', 1)
        # str .format not working on this version
        fileName = '%s-%s%s.%s' % (fileName[0], date, '.'+tag if tag else '', fileName[1])
        DISCHARGE_CSV_FILE_PATH = os.path.join(OUTPUT_DIR, fileName)
        print 'Open Discharge CSV ::', DISCHARGE_CSV_FILE_PATH
        csvWriter = csv.writer(open(DISCHARGE_CSV_FILE_PATH, 'w'), delimiter=',', quotechar='|')
        
        flow = myDss.get('//HANWELLA/FLOW//1HOUR/RUN:RUN 1/', 1)

        if flow.numberValues == 0 :
            MessageBox.showError('No Data', 'Error')
        else :
            csvWriter.writerow(['Location Ids', 'Hanwella'])
            csvWriter.writerow(['Time', 'Flow'])

            # print flow.values[:10]
            # print flow.times[:10]

            csvList = []

            for i in range(0, flow.numberValues) :
                # print int(flow.times[i])
                time = HecTime()
                time.set(int(flow.times[i]))
                
                d = [time.year(), '%d' % (time.month(),), '%d' % (time.day(),)]
                t = ['%d' % (time.hour(),), '%d' % (time.minute(),), '%d' % (time.second(),)]
                if(int(t[0]) > 23) :
                    t[0] = '23'
                    dtStr = ':'.join(str(x) for x in d) + ' ' + ':'.join(str(x) for x in t)
                    dt = datetime.datetime.strptime(dtStr, '%Y:%m:%d %H:%M:%S')
                    dt = dt + datetime.timedelta(hours=1)
                else :
                    dtStr = ':'.join(str(x) for x in d) + ' ' + ':'.join(str(x) for x in t)
                    dt = datetime.datetime.strptime(dtStr, '%Y:%m:%d %H:%M:%S')

                csvList.append([dt.strftime('%Y:%m:%d %H:%M:%S'), "%.2f" % flow.values[i]])
                
            print csvList[:10]
            csvWriter.writerows(csvList)

    except Exception, e :
        MessageBox.showError(' '.join(e.args), "Python Error")
    except java.lang.Exception, e :
        MessageBox.showError(e.getMessage(), "Error")
finally :
    myDss.done()
    print '\nCompleted converting ', DSS_OUTPUT_FILE, ' to ', DISCHARGE_CSV_FILE_PATH