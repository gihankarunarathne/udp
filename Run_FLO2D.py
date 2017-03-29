import sys, string, os, datetime
import shutil
from distutils.dir_util import copy_tree

try :
    FLO2D_TEMPLATE = './Template'
    FLO2D_RUN_FOR_PROJECT = './RunForProjectFolder'

    # Default run for current day
    now = datetime.datetime.now()
    if len(sys.argv) > 1 :
        now = datetime.datetime.strptime(sys.argv[1], '%Y-%m-%d')
    date = now.strftime("%Y-%m-%d")
    print('Run FLO2D on', date)
    app = date + '_Kelani'


    try:
        if(os.path.isdir(app)) :
            shutil.rmtree(app)

        copy_tree(FLO2D_TEMPLATE, app)
        copy_tree(FLO2D_RUN_FOR_PROJECT, app)
        print('Copied FLO2D templates')
    # Directories are the same
    except shutil.Error as e:
        print('Directory not copied. Error: %s' % e)
    # Any error saying that the directory doesn't exist
    except OSError as e:
        print('Directory not copied. Error: %s' % e)

    # os.chdir('C:\\LKB\Simulations\\20170321New Kelani')
    # os.system('"C:\\LKB\Simulations\\20170321New Kelani\\FLOPRO.exe"')

except ValueError:
    raise ValueError("Incorrect data format, should be YYYY-MM-DD")
except Exception as e :
    traceback.print_exc()
finally:
    print('Successfully run FLO2D')