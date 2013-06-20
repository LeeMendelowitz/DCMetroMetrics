import gevent
from gevent import Greenlet
import hotCars
import dbUtils
import os
import sys
import subprocess
import argparse
from datetime import datetime

parser = argparse.ArgumentParser()
parser.add_argument('--LIVE', action='store_true') # Tweets are live

class HotCarApp(Greenlet):

    def __init__(self, LIVE=False):
        Greenlet.__init__(self)
        self.SLEEP = 40 # Run every 10 seconds
        self.LIVE = LIVE

    # Run forever
    def _run(self):

        while True:
            try:
                self.tick()
                gevent.sleep(self.SLEEP)
            except Exception as e:
                import traceback
                logFileName = os.path.join(OUTPUT_DIR, 'runHotCarApp.log')
                logFile = open(logFileName, 'a')
                logFile.write('HotCarApp: Caught Exception! %s\n'%str(e))
                tb = traceback.format_exc()
                logFile.write('Traceback:\n%s\n\n'%tb)
                logFile.close()

    def tick(self):

        OUTPUT_DIR = os.environ['OPENSHIFT_DATA_DIR']
        REPO_DIR = os.environ['OPENSHIFT_REPO_DIR']
        SCRIPT_DIR = os.path.join(REPO_DIR, 'scripts')

        logFileName = os.path.join(OUTPUT_DIR, 'runHotCarApp.log')
        logFile = open(logFileName, 'a')
        n = datetime.now()

        timeStr = n.strftime('%d-%B-%Y %H:%M:%S')
        msg = '*'*50 + '\n'
        msg += '%s Running Hot Car App\n'%timeStr
        logFile.write(msg)
        logFile.flush()
        app = os.path.join(SCRIPT_DIR, 'hotCarApp.py') # This file
        cmd = ['python', app]
        if self.LIVE:
            cmd.append('--LIVE')
        p = subprocess.Popen(cmd, stdout = logFile, stderr = logFile)
        ret = p.wait()

        logFile.flush()
        logFile.write('App exited with return code: %i\n\n'%ret)
        logFile.close()

def runOnce(tweetLive=False):
    # Establish connection with the database
    db = dbUtils.getDB()
    # Run one cycle of the hotcar app
    hotCars.tick(db, tweetLive=tweetLive)

if __name__ == '__main__':
    args = parser.parse_args()
    runOnce(tweetLive=args.LIVE)
