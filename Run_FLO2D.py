#!/usr/bin/python

import argparse
import datetime
import os
import shutil
import traceback
from distutils.dir_util import copy_tree

try:
    root_dir = os.path.dirname(os.path.realpath(__file__))

    FLO2D_DIR = 'FLO2D'
    INFLOW_DAT_FILE = 'INFLOW.DAT'
    OUTFLOW_DAT_FILE = 'OUTFLOW.DAT'
    RAINCELL_DAT_FILE = 'RAINCELL.DAT'
    RUN_FLO2D_FILE = 'RUN_FLO2D.json'

    FLO2D_TEMPLATE = os.path.join(root_dir, 'Template')
    FLO2D_RUN_FOR_PROJECT = os.path.join(root_dir, 'RunForProjectFolder')

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--date", help="Date in YYYY-MM. Default is current date.")
    parser.add_argument("--model-dir", help="FLO2D model directory.")
    args = parser.parse_args()
    print('Commandline Options:', args)

    # Default run for current day
    now = datetime.datetime.now()
    if args.date:
        now = datetime.datetime.strptime(args.date, '%Y-%m-%d')
    date = now.strftime("%Y-%m-%d")

    try:
        appDir = os.path.join(root_dir, date + '_Kelani')
        if args.model_dir:
            appDir = os.path.join(root_dir, args.model_dir)

        print('Run FLO2D on', date, ' on dir:', appDir)

        if os.path.isdir(appDir):
            print('Removing Directory:', appDir)
            shutil.rmtree(appDir)

        if not os.path.exists(appDir):
            print('Creating Dir : ', appDir)
            os.makedirs(appDir)

        # NOTE: Copy Templates first, otherwise actual data will be override by Template Samples
        copy_tree(FLO2D_TEMPLATE, appDir)
        copy_tree(FLO2D_RUN_FOR_PROJECT, appDir)
        print('Copied FLO2D templates')

        FLO2D_DIR_PATH = os.path.join(root_dir, FLO2D_DIR)
        # Move INFLOW.DAT, OUTFLOW.DAT, RAINCELL.DAT and RUN_FLO2D files into model dir
        INFLOW_DAT_FILE_PATH = os.path.join(FLO2D_DIR_PATH, INFLOW_DAT_FILE)
        shutil.move(INFLOW_DAT_FILE_PATH, appDir)
        OUTFLOW_DAT_FILE_PATH = os.path.join(FLO2D_DIR_PATH, OUTFLOW_DAT_FILE)
        shutil.move(OUTFLOW_DAT_FILE_PATH, appDir)
        RAINCELL_DAT_FILE_PATH = os.path.join(FLO2D_DIR_PATH, RAINCELL_DAT_FILE)
        shutil.move(RAINCELL_DAT_FILE_PATH, appDir)
        RUN_FLO2D_FILE_PATH = os.path.join(FLO2D_DIR_PATH, RUN_FLO2D_FILE)
        shutil.move(RUN_FLO2D_FILE_PATH, appDir)

    # Directories are the same
    except shutil.Error as e:
        print('Directory not copied. Error: %s' % e)
    # Any error saying that the directory doesn't exist
    except OSError as e:
        print('Directory not copied. Error: %s' % e)
    else:
        print('>>>>>', appDir)
        os.chdir(appDir)
        os.system(os.path.join(appDir, 'FLOPRO.exe'))

except ValueError:
    raise ValueError("Incorrect data format, should be YYYY-MM-DD")
except Exception as e:
    print(e)
    traceback.print_exc()
finally:
    print('Successfully run FLO2D')
