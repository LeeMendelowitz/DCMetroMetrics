#!/usr/bin/env python
# WARNING: Only Openshift should run this module as main. DO NOT run this locally.
# Run test_app for testing purposes.

import imp
import os
import sys
import subprocess
import argparse
import copy

# Test if this an openshift environment.
openshift_envs = [
        "OPENSHIFT_APP_NAME",
        "OPENSHIFT_NAMESPACE",
        "OPENSHIFT_INTERNAL_IP",
        "OPENSHIFT_PYTHON_VERSION",
        "OPENSHIFT_CLOUD_DOMAIN",
        "OPENSHIFT_INTERNAL_PORT"
        ]

if __name__ == "__main__":
    for env in openshift_envs:
        if env not in os.environ:
            msg = "This does not appear to be an OpenShift environment. Run test_app.py for testing."
            raise RuntimeError(msg)

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
from runElevatorApp import ElevatorApp
from hotCarApp import HotCarApp
from webPageGenerator import WebPageGenerator
from restartingGreenlet import RestartingGreenlet
from bottleApp import BottleApp

def run(LIVE=False):

   # Do not run as live unless this module is main
   if __name__ != "__main__":
       LIVE=False

   # Run the web server
   bottleApp = BottleApp()
   bottleApp.start()

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
