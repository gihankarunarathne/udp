#!/usr/bin/python

from hec.script import MessageBox
from hec.heclib.dss import HecDss
from hec.heclib.util import HecTime
from hec.io import TimeSeriesContainer
import java, csv, sys, datetime
sys.path.append("./simplejson-2.5.2")
import simplejson as json

try :
    try :
        print 'Jython version: ', sys.version

        CONFIG = json.loads(open('CONFIG.json').read())
        # print('Config :: ', CONFIG)

        NUM_METADATA_LINES = 2;
        DSS_OUTPUT_FILE = './2008_2_Events/2008_2_Events.dss'
        DISCHARGE_CSV_FILE = 'DailyDischarge.csv'
        OUTPUT_DIR = './OUTPUT'

        if 'DSS_OUTPUT_FILE' in CONFIG :
            DSS_OUTPUT_FILE = CONFIG['DSS_OUTPUT_FILE']
        if 'DISCHARGE_CSV_FILE' in CONFIG :
            DISCHARGE_CSV_FILE = CONFIG['DISCHARGE_CSV_FILE']
        if 'OUTPUT_DIR' in CONFIG :
            OUTPUT_DIR = CONFIG['OUTPUT_DIR']

        # Default run for current day
        now = datetime.datetime.now()
        if len(sys.argv) > 1 : # Or taken from first arg for the program
            now = datetime.datetime.strptime(sys.argv[1], '%Y-%m-%d')
        date = now.strftime("%Y-%m-%d")

        myDss = HecDss.open(DSS_OUTPUT_FILE)
        fileName = DISCHARGE_CSV_FILE.split('.', 1)
        fileName = "%s-%s.%s" % (fileName[0], date, fileName[1])
        DISCHARGE_CSV_FILE_PATH = "%s/%s" % (OUTPUT_DIR, fileName)
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
                
                d = [time.year(), '%02d' % (time.month(),), '%02d' % (time.day(),)]
                t = ['%02d' % (time.hour(),), '%02d' % (time.minute(),), '%02d' % (time.second(),)]
                dateTime = ':'.join(str(x) for x in d) + ' ' + ':'.join(str(x) for x in t)
                csvList.append([dateTime, "%.2f" % flow.values[i]])
                
            print csvList[:10]
            csvWriter.writerows(csvList)

    except Exception, e :
        MessageBox.showError(' '.join(e.args), "Python Error")
    except java.lang.Exception, e :
        MessageBox.showError(e.getMessage(), "Error")
finally :
    myDss.done()
    print '\nCompleted converting ', DSS_OUTPUT_FILE, ' to ', DISCHARGE_CSV_FILE_PATH