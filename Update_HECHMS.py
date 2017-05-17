#!/usr/bin/python3

import sys, traceback, csv, json, datetime, collections, getopt

DSSDateTime = collections.namedtuple('DSSDateTime', ['dateTime', 'date', 'time'])

def usage() :
    usageText = """
Usage: ./Update_HECHMS.py [-d date] [-h -i] [-s sInterval] [-c cInterval] 

-h  --help          Show usage
-d  --date          Date in YYYY-MM. Default is current date.
-i  --init          Create a State while running the HEC-HMS model
-s  --sInterval     (State Interval in minutes) Time period that state should create after start time
-c  --cInterval     (Control Interval in minutes) Time period that HEC-HMS model should run
"""
    print(usageText)

def getDSSDateTime(dateTime) :
    value = dateTime.strftime('%Y:%m:%d %H:%M:%S')
    s = value.split(' ')
    d = s[0].split(':')
    t = s[1].split(':')
    if(int(t[0]) == 0) : # In case of 00:00, mention it as 24:00 of previous day
        dateTimeTmp = dateTime - datetime.timedelta(hours=1)
        date = dateTimeTmp.strftime('%d %B %Y')
        time = dateTimeTmp.strftime('%H:%M')
        time = time.split(':')
        time[0] = '24'
        time = ':'.join(time)
    else :
        date = dateTime.strftime('%d %B %Y')
        time = dateTime.strftime('%H:%M')

    # Removed DSS formating with HEC-HMS upgrading from 3.5 to 4.1
    date = dateTime.strftime('%d %B %Y')
    time = dateTime.strftime('%H:%M')

    return DSSDateTime(
        dateTime  = date + ' ' + time,
        date      = date,
        time      = time
    )

try :
    CONFIG = json.loads(open('CONFIG.json').read())
    # print('Config :: ', CONFIG)

    NUM_METADATA_LINES = 3;
    HEC_HMS_CONTROL_FILE = './2008_2_Events/Control_1.control'
    HEC_HMS_RUN_FILE = './2008_2_Events/2008_2_Events.run'
    HEC_HMS_GAGE_FILE = './2008_2_Events/2008_2_Events.gage'
    RAIN_CSV_FILE = 'DailyRain.csv'
    TIME_INTERVAL = 60 # In minutes
    OUTPUT_DIR = './OUTPUT'
    STATE_INTERVAL = 1 * 24 * 60 # In minutes
    CONTROL_INTERVAL = 6 * 24 * 60 # In minutes

    if 'HEC_HMS_CONTROL' in CONFIG :
        HEC_HMS_CONTROL_FILE = CONFIG['HEC_HMS_CONTROL']
    if 'HEC_HMS_RUN' in CONFIG :
        HEC_HMS_RUN_FILE = CONFIG['HEC_HMS_RUN']
    if 'HEC_HMS_GAGE' in CONFIG :
        HEC_HMS_GAGE_FILE = CONFIG['HEC_HMS_GAGE']
    if 'RAIN_CSV_FILE' in CONFIG :
        RAIN_CSV_FILE = CONFIG['RAIN_CSV_FILE']
    if 'TIME_INTERVAL' in CONFIG :
        TIME_INTERVAL = CONFIG['TIME_INTERVAL']
    if 'OUTPUT_DIR' in CONFIG :
            OUTPUT_DIR = CONFIG['OUTPUT_DIR']

    date = ''
    initState = False
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hd:is:c:", ["help", "date=", "backDays=", "init", "sInterval", "cInterval"])
    except getopt.GetoptError:          
        usage()                        
        sys.exit(2)                     
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()                     
            sys.exit()           
        elif opt in ("-d", "--date"):
            date = arg
        elif opt in ("-i", "--init"):
            initState = True
        elif opt in ("-s", "--sInterval"):
            STATE_INTERVAL = int(arg)
        elif opt in ("-cInterval", "--cInterval"):
            CONTROL_INTERVAL = int(arg)

    # Default run for current day
    now = datetime.datetime.now()
    if date :
        now = datetime.datetime.strptime(date, '%Y-%m-%d')
    date = now.strftime("%Y-%m-%d")

    print('Update_HECHMS startTime:', datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ', initState:', initState)

    # Extract Start and End times
    fileName = RAIN_CSV_FILE.split('.', 1)
    fileName = "%s-%s.%s" % (fileName[0], date, fileName[1])
    RAIN_CSV_FILE_PATH = "%s/%s" % (OUTPUT_DIR, fileName)
    csvReader = csv.reader(open(RAIN_CSV_FILE_PATH, 'r'), delimiter=',', quotechar='|')
    csvList = list(csvReader)

    print(csvList[NUM_METADATA_LINES][0])
    print(csvList[-1][0])
    startDateTime = datetime.datetime.strptime(csvList[NUM_METADATA_LINES][0], '%Y-%m-%d %H:%M:%S')
    endDateTime = datetime.datetime.strptime(csvList[-1][0], '%Y-%m-%d %H:%M:%S')

    startDateTimeDSS = getDSSDateTime(startDateTime)
    endDateTimeDSS = getDSSDateTime(endDateTime)
    startDate = startDateTimeDSS.date
    startTime = startDateTimeDSS.time
    endDate = endDateTimeDSS.date
    endTime = endDateTimeDSS.time

    controlEndDateTime = startDateTime + datetime.timedelta(minutes=CONTROL_INTERVAL)
    controlEndDateTimeDSS = getDSSDateTime(controlEndDateTime)
    controlEndDate = controlEndDateTimeDSS.date
    controlEndTime = controlEndDateTimeDSS.time

    #############################################
    # Update Control file                       #
    #############################################
    controlFile = open(HEC_HMS_CONTROL_FILE, 'r')
    controlData = controlFile.readlines()
    controlFile.close()

    controlFile = open(HEC_HMS_CONTROL_FILE, 'w')
    for line in controlData :
        if 'Start Date:' in line :
            s = line[:line.rfind('Start Date:')+11]
            s += ' ' + startDate
            controlFile.write(s + '\n')
        elif 'Start Time:' in line :
            s = line[:line.rfind('Start Time:')+11]
            s += ' ' + startTime
            controlFile.write(s + '\n')
        elif 'End Date:' in line :
            s = line[:line.rfind('End Date:')+9]
            s += ' ' + controlEndDate
            controlFile.write(s + '\n')
        elif 'End Time:' in line :
            s = line[:line.rfind('End Time:')+9]
            s += ' ' + controlEndTime
            controlFile.write(s + '\n')
        elif 'Time Interval:' in line :
            s = line[:line.rfind('Time Interval:')+14]
            s += ' ' + str(TIME_INTERVAL)
            controlFile.write(s + '\n')
        else :
            controlFile.write(line)

    #############################################
    # Update Run file                           #
    #############################################
    runFile = open(HEC_HMS_RUN_FILE, 'r')
    runData = runFile.readlines()
    runFile.close()

    runFile = open(HEC_HMS_RUN_FILE, 'w')
    for line in runData :
        if 'Control:' in line :
            runFile.write(line)
            indent = line[:line.rfind('Control:')]

            saveStateDateTime = startDateTime + datetime.timedelta(minutes=STATE_INTERVAL)
            saveStateDateTimeDSS = getDSSDateTime(saveStateDateTime)
            startStateDateTime = startDateTime - datetime.timedelta(minutes=STATE_INTERVAL)
            line1 = indent + 'Save State Name: State_' + startDateTime.strftime('%Y_%m_%d') + '_To_' + saveStateDateTime.strftime('%Y_%m_%d')
            line2 = indent + 'Save State Date: ' + saveStateDateTimeDSS.date
            line3 = indent + 'Save State Time: ' + saveStateDateTimeDSS.time
            runFile.write(line1 + '\n'); runFile.write(line2 + '\n'); runFile.write(line3 + '\n')

            if not initState :
                line4 = indent + 'Start State Name: State_' + startStateDateTime.strftime('%Y_%m_%d') + '_To_' + startDateTime.strftime('%Y_%m_%d')
                runFile.write(line4 + '\n')

        # Skip Writing these lines
        elif 'Save State At End of Run:' in line :
            continue
        elif 'Save State Name:' in line :
            continue
        elif 'Save State Date:' in line :
            continue
        elif 'Save State Time:' in line :
            continue
        elif 'Start State Name:' in line :
            continue
        else :
            runFile.write(line)

    #############################################
    #Update Gage file                           #
    #############################################
    gageFile = open(HEC_HMS_GAGE_FILE, 'r')
    gageData = gageFile.readlines()
    gageFile.close()

    gageFile = open(HEC_HMS_GAGE_FILE, 'w')
    for line in gageData :
        if 'Start Time:' in line :
            s = line[:line.rfind('Start Time:')+11]
            s += ' ' + startDate + ', ' + startTime
            gageFile.write(s + '\n')
        elif 'End Time:' in line :
            s = line[:line.rfind('End Time:')+9]
            s += ' ' + endDate + ', ' + endTime
            gageFile.write(s + '\n')
        else :
            gageFile.write(line)


except Exception as e :
    traceback.print_exc()
finally:
    controlFile.close()
    print('Updated HEC-HMS Control file ', HEC_HMS_CONTROL_FILE, HEC_HMS_RUN_FILE, HEC_HMS_GAGE_FILE)