#!/usr/bin/python3

import sys, datetime, subprocess, argparse, time
from subprocess import Popen

try :
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--file-path", help="File name to be executed.", required=True)
    parser.add_argument("-s", "--start-date", help="Start Date in YYYY-MM-DD.", required=True)
    parser.add_argument("--start-time", help="Start Time in HH:MM:SS.")
    parser.add_argument("-e", "--end-date", help="End Date in YYYY-MM.", required=True)
    parser.add_argument("--end-time", help="End Time in HH:MM:SS.")
    parser.add_argument("-f", "--force", action='store_true', help="Force insert.")
    parser.add_argument("--exec", help="Executor that going to run the file.script. Default `python`. E.g: python3")
    parser.add_argument("-i", "--interval", help="Time Interval between two events in hours")
    parser.add_argument("--wait-before", help="Wait time before running the task in seconds")
    parser.add_argument("-w", "--wait", help="Wait time for complete the task before run for next event in seconds")
    args = parser.parse_args()
    print('Commandline Options:', args)

    timeInterval = 24
    waitBeforeTime = 0
    waitTime = 0

    if not args.file_path and args.start_date and args.end_date :
        print('All fields required.')
        sys.exit(2)
    if args.interval :
        timeInterval = int(args.interval)
    if args.wait_before :
        waitBeforeTime = int(args.wait_before)
    if args.wait :
        waitTime = int(args.wait)

    startDate = datetime.datetime.strptime(args.start_date, '%Y-%m-%d')
    endDate = datetime.datetime.strptime(args.end_date, '%Y-%m-%d')
    if args.start_time :
        startDate = datetime.datetime.strptime("%s %s" % (args.start_date, args.start_time), '%Y-%m-%d %H:%M:%S')
    if args.end_time :
        endDate = datetime.datetime.strptime("%s %s" % (args.end_date, args.end_time), '%Y-%m-%d %H:%M:%S')

    executor = "python"
    if args.exec :
        executor = args.exec

    while(startDate <= endDate) :
        if waitBeforeTime > 0 : time.sleep(waitBeforeTime)
        execList = [executor, args.file_path]
        execList = execList + ['-d' , startDate.strftime("%Y-%m-%d")]
        if args.force :
            execList = execList + ['-f']
        print('*********************************************************')
        print('>>>', execList, '\n')
        proc = Popen(execList, stdout=sys.stdout)
        proc.wait()
        if waitTime > 0 : time.sleep(waitTime)
        print('\n\n')

        startDate = startDate + datetime.timedelta(hours=timeInterval)

except ValueError:
    raise ValueError("Incorrect data format, should be YYYY-MM-DD")
except Exception as e :
    traceback.print_exc()
finally:
    print('Successfully run Script Repeator !.')