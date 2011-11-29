from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from SocketServer import ThreadingMixIn
import threading
import cgi
from urlparse import urlparse, parse_qs
import logging

logger = logging.getLogger('pygsm_gateway.http')

class PygsmHttpServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""

    def __init__(self, address, send_method):
        class Handler(BaseHTTPRequestHandler):
            _send_method = send_method
            def do_POST(self):
                logger.debug('got POST')
                form = cgi.FieldStorage(
                    fp=self.rfile, 
                    headers=self.headers,
                    environ={'REQUEST_METHOD': 'POST',
                             'CONTENT_TYPE': self.headers['Content-Type'],
                             })
                if 'identity' in form and 'text' in form:
                    self._send_method(form['identity'].value,
                                      form['text'].value)
                    self.send_response(200)
                else:
                    self.send_response(400)
                self.end_headers()
                self.wfile.write('\n')
                return

            #added to play nicely with rapidsms_httprouter, although this perhaps is semantically incorrect.
            def do_GET(self):
                logger.debug('got GET')
                #import pdb; pdb.set_trace()
                form = parse_qs(urlparse(self.path).query)
                if 'identity' in form and 'text' in form:
                    self._send_method(form['identity'][0],
                                      form['text'][0])
                    self.send_response(200)
                else:
                    self.send_response(400)
                self.end_headers()
                self.wfile.write('\n')
                return

        HTTPServer.__init__(self, address, Handler)
