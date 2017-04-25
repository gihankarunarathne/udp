#!/usr/bin/python

import sys, string, os, datetime. shutil
from distutils.dir_util import copy_tree

try :
    CWD = os.getcwd()
    FLO2D_TEMPLATE = os.path.join(CWD, 'Template')
    FLO2D_RUN_FOR_PROJECT = os.path.join(CWD, 'RunForProjectFolder')

    # Default run for current day
    now = datetime.datetime.now()
    if len(sys.argv) > 1 :
        now = datetime.datetime.strptime(sys.argv[1], '%Y-%m-%d')
    date = now.strftime("%Y-%m-%d")
    print('Run FLO2D on', date)
    appDir = os.path.join(CWD, date + '_Kelani')

    try:
        # if(os.path.isdir(appDir)) :
        #     shutil.rmtree(appDir)

        copy_tree(FLO2D_TEMPLATE, appDir)
        copy_tree(FLO2D_RUN_FOR_PROJECT, appDir)
        print('Copied FLO2D templates')
    # Directories are the same
    except shutil.Error as e:
        print('Directory not copied. Error: %s' % e)
    # Any error saying that the directory doesn't exist
    except OSError as e:
        print('Directory not copied. Error: %s' % e)
    else:
        os.chdir(appDir)
        os.system(os.path.join(appDir, 'FLOPRO.exe'))

except ValueError:
    raise ValueError("Incorrect data format, should be YYYY-MM-DD")
except Exception as e :
    traceback.print_exc()
finally:
    print('Successfully run FLO2D')
