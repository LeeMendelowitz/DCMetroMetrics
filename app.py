#!/usr/bin/env python
import imp
import os
import sys
import subprocess
import argparse

PY_DIR = os.environ['OPENSHIFT_PYTHON_DIR']
REPO_DIR = os.environ['OPENSHIFT_REPO_DIR']
SCRIPT_DIR = os.path.join(REPO_DIR, 'scripts')

try:
   zvirtenv = os.path.join(PY_DIR, 'virtenv', 'bin', 'activate_this.py')
   execfile(zvirtenv, dict(__file__ = zvirtenv) )
except IOError:
   pass

# Import modules
import gevent
from gevent import Greenlet
from gevent import monkey; monkey.patch_all() # Needed for bottle

# Import application modules
sys.path.append(SCRIPT_DIR)
from runTwitterApp import TwitterApp
from hotCarApp import HotCarApp

##########################################
# Run the Twitter App as a Greenlet. This allows
# us to run the app concurrently with the WSGI server.
class TwitterApp(Greenlet):

    def __init__(self, LIVE=False):
        Greenlet.__init__(self)
        self.LIVE = LIVE # Tweet if True

    def _run(self):
        while True:
            runTwitterApp.runOnce(LIVE=self.LIVE)
            gevent.sleep(runTwitterApp.SLEEP)

def run(LIVE=False):
   ip   = os.environ['OPENSHIFT_INTERNAL_IP']
   port = 8080

   # Load the bottleApp module
   bottleAppPath = 'wsgi/bottleApp.py'
   bottleApp = imp.load_source('bottleApp', bottleAppPath)

   # Run MetroEsclaators twitter App
   twitterApp = TwitterApp(LIVE=LIVE)
   twitterApp.start()

   # Run HotCar twitter app
   hotCarApplication = HotCarApp(LIVE=LIVE)
   hotCarApplication.start()

   # Run the server. Note: This call blocks
   bottle = bottleApp.application
   bottle.run(host=ip, port=port, server=gevent)

   twitterApp.join()
   hotCarApplication.join()

if __name__ == '__main__':
    run(LIVE=True)
