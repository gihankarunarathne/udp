#!/usr/bin/python3

import sys, datetime, subprocess, argparse
from subprocess import Popen

try :
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--file-path", help="File name to be executed.")
    parser.add_argument("-s", "--start-date", help="Start Date in YYYY-MM.")
    parser.add_argument("-e", "--end-date", help="End Date in YYYY-MM.")
    parser.add_argument("-f", "--force", action='store_true', help="Force insert.")
    parser.add_argument("-v", "--version", help="Python version. eg: python3")
    args = parser.parse_args()
    print('Commandline Options:', args)

    if not args.file_path and args.start_date and args.end_date :
        print('All fields required.')
        sys.exit(2)

    startDate = datetime.datetime.strptime(args.start_date, '%Y-%m-%d')
    endDate = datetime.datetime.strptime(args.end_date, '%Y-%m-%d')

    pythonV = "python"
    if args.version :
        pythonV = args.version

    while(startDate <= endDate) :
        execList = [pythonV, args.file_path]
        execList = execList + ['-d' , startDate.strftime("%Y-%m-%d")]
        if args.force :
            execList = execList + ['-f']
        print('*********************************************************')
        print('>>>', execList, '\n')
        proc = Popen(execList, stdout=sys.stdout)
        proc.wait()
        print('\n\n')

        startDate = startDate + datetime.timedelta(days=1)

except ValueError:
    raise ValueError("Incorrect data format, should be YYYY-MM-DD")
except Exception as e :
    traceback.print_exc()
finally:
    print('Successfully run Script Repeator !.')