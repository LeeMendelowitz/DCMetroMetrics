#!/usr/bin/env python
"""
This is the main program run on the Openshift platform.
Running this module will cause the twitter accounts to 
live tweet.

For testing purposes, run the test_app.py program, which
disables live tweeting.
"""

import imp
import os
import sys
import subprocess
import argparse
import copy

if __name__ == "__main__":
    import utils
    if not utils.isOpenshiftEnv():
        msg = "This does not appear to be an OpenShift environment. Run test/test_app.py for testing."
        raise RuntimeError(msg)

PY_DIR = os.environ['PYTHON_DIR']
REPO_DIR = os.environ['REPO_DIR']
SCRIPT_DIR = os.path.join(REPO_DIR, 'scripts')
DATA_DIR = os.environ['DATA_DIR']

# Activate the OpenShift VirtualEnv
try:
   zvirtenv = os.path.join(PY_DIR, 'virtenv', 'bin', 'activate_this.py')
   execfile(zvirtenv, dict(__file__ = zvirtenv) )
except IOError:
   pass

# Import application modules
from escalatorApp import EscalatorApp
from elevatorApp import ElevatorApp
from hotCarApp import HotCarApp

# Import the web server and web page generator
import gevent
from gevent import monkey; monkey.patch_all() # Needed for bottle
from dcmetrometrics.web.server import Server
from dcmetrometrics.web.WebPageGenerator import WebPageGenerator

def run(LIVE=False):

   # Do not run as live unless this module is main
   if __name__ != "__main__":
       LIVE=False

   # Run the web server
   serverApp = Server()
   serverApp.start()

   # Run MetroEscalators twitter App
   escalatorApp = EscalatorApp(LIVE=LIVE)
   escalatorApp.start()

   # Run MetroElevators twitter App
   elevatorApp = ElevatorApp(LIVE=LIVE)
   elevatorApp.start()

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
