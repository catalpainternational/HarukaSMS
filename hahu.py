import time
import sys
import os


sys.path.append(os.getcwd()+"/site-packages")
sys.path.append(os.getcwd())

from django.core.management import setup_environ, ManagementUtility
import settings
setup_environ(settings)

if __name__ == '__main__':

    utility = ManagementUtility()
    command = utility.fetch_command('runwsgiserver')
    command.execute(use_reloader=False)
