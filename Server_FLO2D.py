#!/usr/bin/python

import os, json, subprocess, datetime, traceback, shutil, sys
from os import curdir
from os.path import join as pjoin
from http.server import BaseHTTPRequestHandler, HTTPServer
from sys import executable
from subprocess import Popen

CONFIG = json.loads(open('CONFIG.json').read())
print('Server Configurations :: ', CONFIG)
HOST_ADDRESS = ''
HOST_PORT = 8080
if 'HOST_ADDRESS' in CONFIG :
    HOST_ADDRESS = CONFIG['HOST_ADDRESS']
if 'HOST_PORT' in CONFIG :
    HOST_PORT = CONFIG['HOST_PORT']

INFLOW_DAT_FILE='INFLOW.DAT'
RAINCELL_DAT_FILE='RAINCELL.DAT'
RUN_FLO2D='RUN_FLO2D'
EXTRACT_WATERLEVEL_GRID='EXTRACT_WATERLEVEL_GRID'
EXTRACT_WATERLEVEL='EXTRACT_WATERLEVEL'

# Refer: http://stackoverflow.com/a/13146494/1461060
class StoreHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path == '/'+INFLOW_DAT_FILE:
            store_path = pjoin(curdir, INFLOW_DAT_FILE)
            with open(self.store_path) as fh:
                self.send_response(200)
                self.send_header('Content-type', 'text/json')
                self.end_headers()
                self.wfile.write(fh.read().encode())

    def do_POST(self):
        # Handle INFLOW.DAT file
        if self.path.startswith('/'+INFLOW_DAT_FILE):
            date = self.path[len('/'+INFLOW_DAT_FILE)+1:]
            print('POST request on ', self.path, date)
            length = self.headers['content-length']
            data = self.rfile.read(int(length))
            # print('DATA:', data)

            FLO2D_DIR_PATH = os.path.join(curdir, date + '_Kelani')
            # If Dir already exists, cleanup
            #TODO: Handle in a proper way
            if(os.path.isdir(FLO2D_DIR_PATH)):
                shutil.rmtree(FLO2D_DIR_PATH)
            # Create FLO2D Directory for new simulation
            if not os.path.exists(FLO2D_DIR_PATH):
                os.makedirs(FLO2D_DIR_PATH)
            INFLOW_DAT_FILE_PATH = pjoin(FLO2D_DIR_PATH, INFLOW_DAT_FILE)

            inflowFile = open(INFLOW_DAT_FILE_PATH, 'w')
            inflowFile.write(data.decode())
            inflowFile.close()

            self.send_response(200)
            self.send_header('Content-type', 'text/json')
            self.end_headers()

        # Handle RAINCELL.DAT file
        elif self.path.startswith('/'+RAINCELL_DAT_FILE):
            date = self.path[len('/'+RAINCELL_DAT_FILE)+1:]
            print('POST request on ', self.path, date)
            length = self.headers['content-length']
            data = self.rfile.read(int(length))
            # print('DATA:', data)

            FLO2D_DIR_PATH = os.path.join(curdir, date + '_Kelani')
            # Create FLO2D Directory for new simulation
            if not os.path.exists(FLO2D_DIR_PATH):
                os.makedirs(FLO2D_DIR_PATH)
            RAINCELL_DAT_FILE_PATH = pjoin(FLO2D_DIR_PATH, RAINCELL_DAT_FILE)

            raincellFile = open(RAINCELL_DAT_FILE_PATH, 'w')
            raincellFile.write(data.decode())
            raincellFile.close()

            self.send_response(200)
            self.send_header('Content-type', 'text/json')
            self.end_headers()

        # Run FLO2D application
        elif self.path.startswith('/'+RUN_FLO2D):
            date = self.path[len('/'+RUN_FLO2D)+1:]
            print('POST request on ', self.path, date)

            try :
                # Execute FLO2D
                print('Execute FLO2D ...')
                if len(date) > 0 :
                     Popen([executable, 'Run_FLO2D.py', date], creationflags=subprocess.CREATE_NEW_CONSOLE)
                else :
                    Popen([executable, 'Run_FLO2D.py'], creationflags=subprocess.CREATE_NEW_CONSOLE)
                #os.system('python Run_FLO2D.py'+ date)
                #os.system('python Run_FLO2D.py')

                self.send_response(200)
                self.send_header('Content-type', 'text/json')
                self.end_headers()
            except Exception as e :
                traceback.print_exc()
                self.send_response(500)
                self.end_headers()

        # Run WATERLEVEL GRID extraction from BASE.OUT
        elif self.path.startswith('/'+EXTRACT_WATERLEVEL_GRID):
            date = self.path[len('/'+EXTRACT_WATERLEVEL_GRID)+1:]
            print('POST request on ', self.path, date)

            try :
                # Execute WATERLEVEL GRID extraction
                print('Execute WATERLEVEL GRID extraction ...')
                if len(date) > 0 :
                    Popen(["powershell.exe", '.\CopyWaterLevelGridToCMS.ps1', '-d', date], stdout=sys.stdout)
                    #os.system('python CopyWaterLevelGridToCMS.ps1 '+ date)
                else :
                    Popen(["powershell.exe", '.\CopyWaterLevelGridToCMS.ps1'], stdout=sys.stdout)
                    #os.system('python CopyWaterLevelGridToCMS.ps1 ')

                self.send_response(200)
                self.send_header('Content-type', 'text/json')
                self.end_headers()
            except Exception as e :
                traceback.print_exc()
                self.send_response(500)
                self.end_headers()

        # Run FLO2D WATERLEVEL extraction from HYCHAN.OUT
        elif self.path.startswith('/'+EXTRACT_WATERLEVEL):
            date = self.path[len('/'+EXTRACT_WATERLEVEL)+1:]
            print('POST request on ', self.path, date)

            length = self.headers['content-length']
            data = self.rfile.read(int(length))
            runConfig = json.loads(data.decode())
            print('RUN FLO2D options:', runConfig)

            try :
                # Execute WATERLEVEL extraction
                print('Execute WATERLEVEL extraction ...')
                execList = ["powershell.exe", '.\CopyWaterLevelToCMS.ps1']
                if len(date) > 0 :
                    execList = execList + ['-d' , date]
                if runConfig.get('FLO2D_PATH') :
                    execList = execList + ['-p' , runConfig.get('FLO2D_PATH')]
                print('exec List:', execList)

                Popen(execList, stdout=sys.stdout)
                #os.system('python CopyWaterLevelToCMS.ps1 '+ date)

                self.send_response(200)
                self.send_header('Content-type', 'text/json')
                self.end_headers()
            except Exception as e :
                traceback.print_exc()
                self.send_response(500)
                self.end_headers()


server = HTTPServer((HOST_ADDRESS, HOST_PORT), StoreHandler)
server.serve_forever()
