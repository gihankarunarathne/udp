#!/usr/bin/python

import json
import os
import subprocess
import sys
import traceback
from http.server import BaseHTTPRequestHandler, HTTPServer
from os import curdir
from os.path import join as pjoin
from subprocess import Popen
from sys import executable

root_dir = os.path.dirname(os.path.realpath(__file__))
CONFIG = json.loads(open(pjoin(root_dir, './CONFIG.json')).read())
print('Server Configurations :: ', CONFIG)
HOST_ADDRESS = ''
HOST_PORT = 8080
if 'HOST_ADDRESS' in CONFIG:
    HOST_ADDRESS = CONFIG['HOST_ADDRESS']
if 'HOST_PORT' in CONFIG:
    HOST_PORT = CONFIG['HOST_PORT']

FLO2D_DIR = 'FLO2D'
INFLOW_DAT_FILE = 'INFLOW.DAT'
RAINCELL_DAT_FILE = 'RAINCELL.DAT'
RUN_FLO2D = 'RUN_FLO2D'
RUN_FLO2D_FILE = 'RUN_FLO2D.json'
EXTRACT_WATERLEVEL_GRID = 'EXTRACT_WATERLEVEL_GRID'
EXTRACT_WATERLEVEL = 'EXTRACT_WATERLEVEL'
EXTRACT_WATER_DISCHARGE = 'EXTRACT_WATER_DISCHARGE'


# Refer: http://stackoverflow.com/a/13146494/1461060
class StoreHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path == '/'+INFLOW_DAT_FILE:
            store_path = pjoin(curdir, INFLOW_DAT_FILE)
            with open(store_path) as fh:
                self.send_response(200)
                self.send_header('Content-type', 'text/json')
                self.end_headers()
                self.wfile.write(fh.read().encode())
            return

    def do_POST(self):
        # Handle INFLOW.DAT file
        if self.path.startswith('/'+INFLOW_DAT_FILE):
            date = self.path[len('/'+INFLOW_DAT_FILE)+1:]
            print('POST request on ', self.path, date)
            length = self.headers['content-length']
            data = self.rfile.read(int(length))
            # print('DATA:', data)

            flo2d_dir_path = os.path.join(curdir, FLO2D_DIR)
            # Temporary write into FLO2D dir. Later move into FLO2D model dir while Running the model.
            inflow_dat_file_path = pjoin(flo2d_dir_path, INFLOW_DAT_FILE)

            inflow_file = open(inflow_dat_file_path, 'w')
            inflow_file.write(data.decode())
            inflow_file.close()

            self.send_response(200)
            self.send_header('Content-type', 'text/json')
            self.end_headers()
            return

        # Handle RAINCELL.DAT file
        elif self.path.startswith('/'+RAINCELL_DAT_FILE):
            date = self.path[len('/'+RAINCELL_DAT_FILE)+1:]
            print('POST request on ', self.path, date)
            length = self.headers['content-length']
            data = self.rfile.read(int(length))
            # print('DATA:', data)

            flo2d_dir_path = os.path.join(curdir, FLO2D_DIR)
            # Temporary write into FLO2D dir. Later move into FLO2D model dir while Running the model.
            raincell_dat_file_path = pjoin(flo2d_dir_path, RAINCELL_DAT_FILE)

            raincell_file = open(raincell_dat_file_path, 'w')
            raincell_file.write(data.decode())
            raincell_file.close()

            self.send_response(200)
            self.send_header('Content-type', 'text/json')
            self.end_headers()
            return

        # Run FLO2D application
        elif self.path.startswith('/'+RUN_FLO2D):
            date = self.path[len('/'+RUN_FLO2D)+1:]
            print('POST request on ', self.path, date)

            length = self.headers['content-length']
            data = self.rfile.read(int(length))
            run_config = json.loads(data.decode())
            print('RUN FLO2D: RUN FLO2D options:', run_config)

            flo2d_dir_path = os.path.join(curdir, FLO2D_DIR)
            # Temporary write into FLO2D dir. Later move into FLO2D model dir while Running the model.
            run_flo2d_file_path = pjoin(flo2d_dir_path, RUN_FLO2D_FILE)
            with open(run_flo2d_file_path, 'w') as runFLO2DFile:
                json.dump(run_config, runFLO2DFile)

            try:
                # Execute FLO2D
                print('Execute FLO2D ...')
                exec_list = [executable, pjoin(root_dir, 'Run_FLO2D.py')]

                if len(date) > 0:
                    exec_list = exec_list + ['-d', date]
                if run_config.get('FLO2D_PATH'):
                    exec_list = exec_list + ['--model-dir', run_config.get('FLO2D_PATH')]
                print('exec List:', exec_list)

                # Popen(execList, shell=True)
                Popen(exec_list, creationflags=subprocess.CREATE_NEW_CONSOLE)
                # Popen(execList, stdout=sys.stdout)
                # os.system('python Run_FLO2D.py'+ date)
                self.send_response(200)
                self.send_header('Content-type', 'text/json')
                self.end_headers()
                return
            except Exception as e:
                print(e)
                traceback.print_exc()
                self.send_response(500)
                self.end_headers()

        # Run WATERLEVEL GRID extraction from BASE.OUT
        elif self.path.startswith('/'+EXTRACT_WATERLEVEL_GRID):
            date = self.path[len('/'+EXTRACT_WATERLEVEL_GRID)+1:]
            print('POST request on ', self.path, date)

            length = self.headers['content-length']
            data = self.rfile.read(int(length))
            run_config = json.loads(data.decode())
            print('WATER_LEVEL_GRID: RUN FLO2D options:', run_config)

            try:
                # Execute WATERLEVEL GRID extraction
                print('Execute WATERLEVEL GRID extraction ...')
                exec_list = ["powershell.exe", pjoin(root_dir, '.\CopyWaterLevelGridToCMS.ps1')]
                if len(date) > 0:
                    exec_list = exec_list + ['-date', date]
                if run_config.get('MODEL_STATE_TIME'):
                    exec_list = exec_list + ['-time', run_config.get('MODEL_STATE_TIME')]

                if run_config.get('TIMESERIES_START_DATE'):
                    exec_list = exec_list + ['-start_date', run_config.get('TIMESERIES_START_DATE')]
                if run_config.get('TIMESERIES_START_TIME'):
                    exec_list = exec_list + ['-start_time', run_config.get('TIMESERIES_START_TIME')]

                if run_config.get('FLO2D_PATH'):
                    exec_list = exec_list + ['-path', run_config.get('FLO2D_PATH')]
                if run_config.get('FLO2D_OUTPUT_SUFFIX'):
                    exec_list = exec_list + ['-out', run_config.get('FLO2D_OUTPUT_SUFFIX')]

                if run_config.get('RUN_NAME'):
                    exec_list = exec_list + ['-name', run_config.get('RUN_NAME')]

                print('exec List:', exec_list)

                Popen(exec_list, stdout=sys.stdout)
                # os.system('python CopyWaterLevelGridToCMS.ps1 '+ date)

                self.send_response(200)
                self.send_header('Content-type', 'text/json')
                self.end_headers()
                return
            except Exception as e:
                print(e)
                traceback.print_exc()
                self.send_response(500)
                self.end_headers()

        # Run FLO2D WATERLEVEL extraction from HYCHAN.OUT
        elif self.path.startswith('/'+EXTRACT_WATERLEVEL):
            date = self.path[len('/'+EXTRACT_WATERLEVEL)+1:]
            print('POST request on ', self.path, date)

            length = self.headers['content-length']
            data = self.rfile.read(int(length))
            run_config = json.loads(data.decode())
            print('WATER_LEVEL: RUN FLO2D options:', run_config)

            try:
                # Execute WATERLEVEL extraction
                print('Execute WATERLEVEL extraction ...')
                exec_list = ["powershell.exe", pjoin(root_dir, '.\CopyWaterLevelToCMS.ps1')]
                if len(date) > 0:
                    exec_list = exec_list + ['-date', date]
                if run_config.get('MODEL_STATE_TIME'):
                    exec_list = exec_list + ['-time', run_config.get('MODEL_STATE_TIME')]

                if run_config.get('TIMESERIES_START_DATE'):
                    exec_list = exec_list + ['-start_date', run_config.get('TIMESERIES_START_DATE')]
                if run_config.get('TIMESERIES_START_TIME'):
                    exec_list = exec_list + ['-start_time', run_config.get('TIMESERIES_START_TIME')]

                if run_config.get('FLO2D_PATH'):
                    exec_list = exec_list + ['-path', run_config.get('FLO2D_PATH')]
                if run_config.get('FLO2D_OUTPUT_SUFFIX'):
                    exec_list = exec_list + ['-out', run_config.get('FLO2D_OUTPUT_SUFFIX')]

                if run_config.get('RUN_NAME'):
                    exec_list = exec_list + ['-name', run_config.get('RUN_NAME')]
                # TODO: Handle passing forceInsert
                exec_list = exec_list + ['-forceInsert', "True"]

                print('exec List:', exec_list)

                Popen(exec_list, stdout=sys.stdout)
                # os.system('python CopyWaterLevelToCMS.ps1 '+ date)

                self.send_response(200)
                self.send_header('Content-type', 'text/json')
                self.end_headers()
                return
            except Exception as e:
                print(e)
                traceback.print_exc()
                self.send_response(500)
                self.end_headers()

        # Run FLO2D WATER DISCHARGE extraction from HYCHAN.OUT
        elif self.path.startswith('/' + EXTRACT_WATER_DISCHARGE):
            date = self.path[len('/' + EXTRACT_WATER_DISCHARGE) + 1:]
            print('POST request on ', self.path, date)

            length = self.headers['content-length']
            data = self.rfile.read(int(length))
            run_config = json.loads(data.decode())
            print('WATER_DISCHARGE: RUN FLO2D options:', run_config)

            try:
                # Execute WATER DISCHARGE extraction
                print('Execute WATER DISCHARGE extraction ...')
                exec_list = ["powershell.exe", pjoin(root_dir, '.\CopyFLO2DDischargeToCMS.ps1')]
                if len(date) > 0:
                    exec_list = exec_list + ['-date', date]
                if run_config.get('MODEL_STATE_TIME'):
                    exec_list = exec_list + ['-time', run_config.get('MODEL_STATE_TIME')]

                if run_config.get('TIMESERIES_START_DATE'):
                    exec_list = exec_list + ['-start_date', run_config.get('TIMESERIES_START_DATE')]
                if run_config.get('TIMESERIES_START_TIME'):
                    exec_list = exec_list + ['-start_time', run_config.get('TIMESERIES_START_TIME')]

                if run_config.get('FLO2D_PATH'):
                    exec_list = exec_list + ['-path', run_config.get('FLO2D_PATH')]
                if run_config.get('FLO2D_OUTPUT_SUFFIX'):
                    exec_list = exec_list + ['-out', run_config.get('FLO2D_OUTPUT_SUFFIX')]

                if run_config.get('RUN_NAME'):
                    exec_list = exec_list + ['-name', run_config.get('RUN_NAME')]
                # TODO: Handle passing forceInsert
                exec_list = exec_list + ['-forceInsert', "True"]

                print('exec List:', exec_list)
                Popen(exec_list, stdout=sys.stdout)

                self.send_response(200)
                self.send_header('Content-type', 'text/json')
                self.end_headers()
                return
            except Exception as e:
                print(e)
                traceback.print_exc()
                self.send_response(500)
                self.end_headers()


server = HTTPServer((HOST_ADDRESS, HOST_PORT), StoreHandler)
server.serve_forever()
