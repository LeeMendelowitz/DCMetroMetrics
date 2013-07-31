#!/usr/bin/env python

# This runs the @MetroElevators Twitter App
# It also downloads elevator data from the WMATA API
# and stores the escalator statuses in the database

# This module can be executed directly for local testing
#######################################################

if __name__ == "__main__":
    # Local Testing
    import test_setup
    test_setup.setupPaths()

import os
import sys
import subprocess
from datetime import datetime
import gevent
from gevent import Greenlet
from restartingGreenlet import RestartingGreenlet
from elevatorApp import ElevatorApp as App

OUTPUT_DIR = os.environ.get('OPENSHIFT_DATA_DIR', None)
if OUTPUT_DIR is None:
    OUTPUT_DIR = os.getcwd()

REPO_DIR = os.environ.get('OPENSHIFT_REPO_DIR', None)
if REPO_DIR is None:
    SCRIPT_DIR = os.getcwd()
else:
    SCRIPT_DIR = os.path.join(REPO_DIR, 'scripts')
DATA_DIR = os.environ['OPENSHIFT_DATA_DIR']

SLEEP = 30

##########################################
# Run the Twitter App as a Greenlet.
class ElevatorApp(RestartingGreenlet):

    def __init__(self, SLEEP=SLEEP, LIVE=False):
        RestartingGreenlet.__init__(self, SLEEP=SLEEP, LIVE=LIVE)
        self.LIVE = LIVE # Tweet only if Live
        self.SLEEP = SLEEP # Sleep time after each tick
        self.logFileName = os.path.join(DATA_DIR, 'runElevatorApp.log')

    def _run(self):
        while True:
            try:
                self.tick()
            except Exception as e:
                import traceback
                logFile = open(self.logFileName, 'a')
                logFile.write('ElevatorApp caught Exception: %s\n'%(str(e)))
                tb = traceback.format_exc()
                logFile.write('Traceback:\n%s\n\n'%tb)
                logFile.close()
            gevent.sleep(self.SLEEP)

    def tick(self):

        # Run MetroElevators twitter App
        with open(self.logFileName, 'a') as logFile:

            n = datetime.now()
            timeStr = n.strftime('%d-%B-%Y %H:%M:%S')

            msg = '*'*50 + '\n'
            msg += '%s Elevator App Tick\n'%timeStr
            msg += 'App Mode: %s\n'%('LIVE' if self.LIVE else 'NOT LIVE')

            logFile.write(msg)
            logFile.flush()

            app = App(logFile, LIVE=self.LIVE)
            app.tick()

if __name__ == "__main__":
    print 'Running the elevator app locally....'
    escApp = ElevatorApp()
    escApp.start()
    escApp.join()
