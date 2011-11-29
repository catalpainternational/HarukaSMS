#!/usr/bin/env python
import logging

from http import PygsmHttpServer
from gsm import GsmPollingThread
from serial.tools.list_ports import *
import platform


logger = logging.getLogger()
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

fabulaws_logger = logging.getLogger('pygsm_gateway')
fabulaws_logger.setLevel(logging.DEBUG)


WINDOWS_NAME = 'nt'
HUAWEI_NAME = 'PC UI Interface'


if os.name == WINDOWS_NAME:
    for c in comports():
        if c[1].find('PC UI Interface') != -1:
            port = c[0]
elif platform.platform().startswith('Darwin'):
    port = '/dev/tty.HUAWEIMobile-Modem'
else:
    port = '/dev/tty.USB1'


if __name__ == '__main__':
    args = {
        #'url': 'http://localhost:8000/backend/pygsm-gateway/',
        'url' : 'http://localhost:8000/router/receive',
        'url_args': {},
        'modem_args': {
            'port': port,
            'baudrate': 115200,
            'rtscts': 1,
            'timeout': 10,
        }
    }
    gsm_thread = GsmPollingThread(**args)
    gsm_thread.start()
    server = PygsmHttpServer(('localhost', 8080), gsm_thread.send)
    print 'Starting server, use <Ctrl-C> to stop'
    try:
        server.serve_forever()
    except:
        raise
    finally:
        gsm_thread.running = False
        gsm_thread.join()
