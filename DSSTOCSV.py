from hec.script import MessageBox
from hec.heclib.dss import HecDss
from hec.heclib.util import HecTime
from hec.io import TimeSeriesContainer
import java
import csv
import sys

try :
    try :
        print 'Jython version: ', sys.version
        NUM_METADATA_LINES = 2;
        DSS_FILE_PATH = './2008_2_Events/2008_2_Events.dss'
        CSV_FILE_PATH = 'DailyDischarge.csv'

        myDss = HecDss.open(DSS_FILE_PATH)
        csvWriter = csv.writer(open(CSV_FILE_PATH, 'w'), delimiter=',', quotechar='|')
        
        flow = myDss.get('//HANWELLA/FLOW//1DAY/RUN:RUN 1/', 1)

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
    print '\nCompleted converting ', DSS_FILE_PATH, ' to ', CSV_FILE_PATH