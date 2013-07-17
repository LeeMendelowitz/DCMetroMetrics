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

# Activate the OpenShift VirtualEnv
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
from bottleApp import BottleApp

def run(LIVE=False):

   # Run the web server
   bottleApp = BottleApp()
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
