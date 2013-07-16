#!/usr/bin/env python
import imp
import os
import sys
import subprocess
import argparse
import copy

PY_DIR = os.environ['OPENSHIFT_PYTHON_DIR']
REPO_DIR = os.environ['OPENSHIFT_REPO_DIR']
SCRIPT_DIR = os.path.join(REPO_DIR, 'scripts')
DATA_DIR = os.environ['OPENSHIFT_DATA_DIR']

try:
   zvirtenv = os.path.join(PY_DIR, 'virtenv', 'bin', 'activate_this.py')
   execfile(zvirtenv, dict(__file__ = zvirtenv) )
except IOError:
   pass

# Import modules
import gevent
from gevent import monkey; monkey.patch_all() # Needed for bottle

# Import application modules
sys.path.append(SCRIPT_DIR)
from runEscalatorApp import EscalatorApp
from hotCarApp import HotCarApp
from webPageGenerator import WebPageGenerator
from restartingGreenlet import RestartingGreenlet

#################################################
# Run the bottle app in a greenlet 
class BottleApp(RestartingGreenlet):

    def __init__(self, LIVE=False):
        RestartingGreenlet.__init__(self, LIVE=LIVE)
        # Load the bottleApp module
        self.bottleAppPath = os.path.join(SCRIPT_DIR, 'bottleApp.py')
        self.bottleApp = imp.load_source('bottleApp', self.bottleAppPath)
        self.LIVE=LIVE

    def _run(self):
        try:
            # Run the server.
            ip   = os.environ['OPENSHIFT_INTERNAL_IP']
            port = 8080
            bottle = self.bottleApp.application
            # This call blocks
            bottle.run(host=ip, port=port, server='gevent')

        except Exception as e:
            logName = os.path.join(DATA_DIR, 'bottle.log')
            fout = open(logName, 'a')
            fout.write('Caught Exception while running bottle! %s\n'%(str(e)))
            fout.close()


def run(LIVE=False):

   # Run the web server
   bottleApp = BottleApp(LIVE=LIVE)
   bottleApp.start()

   # Run MetroEsclaators twitter App
   escalatorApp = EscalatorApp(LIVE=LIVE)
   escalatorApp.start()

   # Run HotCar twitter app
   hotCarApplication = HotCarApp(LIVE=LIVE)
   hotCarApplication.start()

   # Run the web page generator
   webPageGenerator = WebPageGenerator()
   webPageGenerator.start()

   # Run forever
   while True:
       gevent.sleep(10)

if __name__ == '__main__':
   run(LIVE=True)
