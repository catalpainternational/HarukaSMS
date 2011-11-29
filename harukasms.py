import time
import webbrowser
import sys
#sys.path.append("haruka")
import threading
from django.core.management import setup_environ, ManagementUtility
import settings
#from pygsm_gateway.pygsm-gateway import *

setup_environ(settings)



class HarukaServer(threading.Thread):
    def __init__(self):
        super(HarukaServer, self).__init__()
        print "Haruka Server instance created"

    def run(self):
        print "Starting Haruka Server..."
        utility = ManagementUtility()
        command = utility.fetch_command('runserver')
        command.execute(use_reloader=False)



if __name__ == '__main__':

    #router = HarukaRouter()
    #router.start()
    #time.sleep(2)

    server = HarukaServer()
    server.start()
    time.sleep(2)

    webbrowser.open('http://localhost:8000')

