import csv
from string import Template
import sys, traceback

try :
    CSV_NUM_METADATA_LINES = 2
    DAT_WIDTH = 12
    CSV_FILE_PATH = 'DailyDischarge.csv'
    DAT_FILE_PATH = './FLO2D/INFLOW.DAT'

    # FLO-2D parameters
    IHOURDAILY  = 1     # 0-hourly interval, 1-daily interval
    IDEPLT      = 77821
    IFC         = 'F'   # foodplain 'F' or a channel 'C'
    INOUTFC     = 0     # 0-inflow, 1-outflow
    KHIN        = 77821 # inflow nodes
    HYDCHAR     = 'H'   # Denote line of inflow hydrograph time and discharge pairs

    csvReader = csv.reader(open(CSV_FILE_PATH, 'r'), delimiter=',', quotechar='|')
    csvList = list(csvReader)

    f = open(DAT_FILE_PATH, 'w')
    line1 = '{0} {1:{w}{b}}\n'.format(IHOURDAILY, IDEPLT, b='d', w=DAT_WIDTH)
    line2 = '{0} {1:{w}{b}} {2:{w}{b}}\n'.format(IFC, INOUTFC, KHIN, b='d', w=DAT_WIDTH)
    line3 = '{0} {1:{w}{b}} {2:{w}{b}}\n'.format(HYDCHAR, 0.0, 0.0, b='.1f', w=DAT_WIDTH)
    f.writelines([line1, line2, line3])

    lines = []; i = 1.0
    for value in csvList[CSV_NUM_METADATA_LINES:]:
        print(i)
        lines.append('{0} {1:{w}{b}} {2:{w}{b}}\n'.format(HYDCHAR, i, float(value[1]), b='.1f', w=DAT_WIDTH))
        i += 1.0

    f.writelines(lines)

except Exception as e :
    traceback.print_exc()
finally:
    f.close()
    print('Completed ', CSV_FILE_PATH, ' to ', DAT_FILE_PATH)