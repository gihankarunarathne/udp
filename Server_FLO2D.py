from os import curdir
from os.path import join as pjoin

from http.server import BaseHTTPRequestHandler, HTTPServer

# Refer: http://stackoverflow.com/a/13146494/1461060
class StoreHandler(BaseHTTPRequestHandler):
    store_path = pjoin(curdir, 'INFLOW.DAT')

    def do_GET(self):
        if self.path == '/INFLOW.DAT':
            with open(self.store_path) as fh:
                self.send_response(200)
                self.send_header('Content-type', 'text/json')
                self.end_headers()
                self.wfile.write(fh.read().encode())

    def do_POST(self):
        if self.path == '/INFLOW.DAT':
            length = self.headers['content-length']
            data = self.rfile.read(int(length))
            print('DATA:', data)

            with open(self.store_path, 'w') as fh:
                fh.write(data.decode())
                fh.close()

            self.send_response(200)
            self.send_header('Content-type', 'text/json')
            self.end_headers()

server = HTTPServer(('', 8080), StoreHandler)
server.serve_forever()