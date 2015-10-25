#!/usr/bin/env python
"""
apps.runEscalatorApp

# This runs the escalatorApp instance.
# This app downloads escalator data from the WMATA API,
# stores escalator statuses in the database, and 
# generates tweets for @MetroEscalators.

# This module can be executed directly for local testing
"""

if __name__ == "__main__":
    # Local Testing
    import test.setup

import os
import sys
import subprocess
from datetime import datetime
import gevent
from gevent import Greenlet

from dcmetrometrics.common.restarting_greenlet import RestartingGreenlet
from dcmetrometrics.eles.escalator_app import EscalatorApp as App
from dcmetrometrics.common.globals import DATA_DIR, REPO_DIR

OUTPUT_DIR = DATA_DIR
if OUTPUT_DIR is None:
    OUTPUT_DIR = os.getcwd()

if REPO_DIR is None:
    SCRIPT_DIR = os.getcwd()
else:
    SCRIPT_DIR = os.path.join(REPO_DIR, 'scripts')

SLEEP = 30

##########################################
# Run the Twitter App as a Greenlet.
class EscalatorApp(RestartingGreenlet):

    def __init__(self, SLEEP=SLEEP, LIVE=False):
        RestartingGreenlet.__init__(self, SLEEP=SLEEP, LIVE=LIVE)
        self.LIVE = LIVE # Tweet only if Live
        self.SLEEP = SLEEP # Sleep time after each tick
        self.logFileName = os.path.join(DATA_DIR, 'runEscalatorApp.log')

    def _run(self):
        while True:
            try:
                self.tick()
            except Exception as e:
                import traceback
                logFile = open(self.logFileName, 'a')
                logFile.write('EscalatorApp caught Exception: %s\n'%(str(e)))
                tb = traceback.format_exc()
                logFile.write('Traceback:\n%s\n\n'%tb)
                logFile.close()
            gevent.sleep(self.SLEEP)

    def tick(self):

        # Run MetroEsclaators twitter App
        with open(self.logFileName, 'a') as logFile:

            n = datetime.now()
            timeStr = n.strftime('%d-%B-%Y %H:%M:%S')

            msg = '*'*50 + '\n'
            msg += '%s Escalator App Tick\n'%timeStr
            msg += 'App Mode: %s\n'%('LIVE' if self.LIVE else 'NOT LIVE')

            logFile.write(msg)
            logFile.flush()

            app = App(logFile, LIVE=self.LIVE)
            app.tick()

if __name__ == "__main__":
    print 'Running the escalator app locally....'
    escApp = EscalatorApp()
    escApp.start()
    escApp.join()
