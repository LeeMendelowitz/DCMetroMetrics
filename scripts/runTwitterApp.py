import os
import sys
import subprocess
from datetime import datetime
import gevent
from gevent import Greenlet
from twitterApp import TwitterApp as App


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
class TwitterApp(Greenlet):

    def __init__(self, SLEEP=SLEEP, LIVE=False):
        Greenlet.__init__(self)
        self.LIVE = LIVE # Tweet only if Live
        self.SLEEP = SLEEP # Sleep time after each tick
        self.logFileName = os.path.join(DATA_DIR, 'runTwitterApp.log')

    def _run(self):
        while True:
            try:
                self.tick()
            except Exception as e:
                logFile = open(self.logFileName, 'a')
                logFile.write('TwitterApp caught Exception: %s\n'%(str(e)))
                logFile.close()
            gevent.sleep(self.SLEEP)

    def tick(self):

        # Run MetroEsclaators twitter App
        with open(self.logFileName, 'a') as logFile:

            n = datetime.now()
            timeStr = n.strftime('%d-%B-%Y %H:%M:%S')

            msg = '*'*50 + '\n'
            msg += '%s Twitter App Tick\n'%timeStr
            msg += 'App Mode: %s\n'%('LIVE' if self.LIVE else 'NOT LIVE')

            logFile.write(msg)
            logFile.flush()

            app = App(logFile, LIVE=self.LIVE)
            app.tick()
