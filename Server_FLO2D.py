#!/usr/bin/python

import os, json, subprocess
from os import curdir
from os.path import join as pjoin
from http.server import BaseHTTPRequestHandler, HTTPServer
from sys import executable
from subprocess import Popen

CONFIG = json.loads(open('CONFIG.json').read())
print('Config :: ', CONFIG)
HOST_ADDRESS = ''
HOST_PORT = 8080
if 'HOST_ADDRESS' in CONFIG :
    HOST_ADDRESS = CONFIG['HOST_ADDRESS']
if 'HOST_PORT' in CONFIG :
    HOST_PORT = CONFIG['HOST_PORT']

INFLOW_DAT_FILE='INFLOW.DAT'

# Refer: http://stackoverflow.com/a/13146494/1461060
class StoreHandler(BaseHTTPRequestHandler):
    store_path = pjoin(curdir, INFLOW_DAT_FILE)

    def do_GET(self):
        if self.path == '/'+INFLOW_DAT_FILE:
            with open(self.store_path) as fh:
                self.send_response(200)
                self.send_header('Content-type', 'text/json')
                self.end_headers()
                self.wfile.write(fh.read().encode())

    def do_POST(self):
        if self.path.startswith('/'+INFLOW_DAT_FILE):
            length = self.headers['content-length']
            data = self.rfile.read(int(length))
            # print('DATA:', data)

            with open(self.store_path, 'w') as fh:
                fh.write(data.decode())
                fh.close()

            self.send_response(200)
            self.send_header('Content-type', 'text/json')
            self.end_headers()

            date = self.path[len('/'+INFLOW_DAT_FILE)+1:]

            try :
                # Execute FLO2D
                if len(date) > 0 :
                     Popen([executable, 'Run_FLO2D.py', date], creationflags=subprocess.CREATE_NEW_CONSOLE)
                else :
                    Popen([executable, 'Run_FLO2D.py'], creationflags=subprocess.CREATE_NEW_CONSOLE)
                #os.system('python Run_FLO2D.py'+ date)
                #os.system('python Run_FLO2D.py')
            except Exception as e :
                traceback.print_exc()

server = HTTPServer((HOST_ADDRESS, HOST_PORT), StoreHandler)
server.serve_forever()
