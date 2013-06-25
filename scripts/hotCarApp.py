import gevent
from restartingGreenlet import RestartingGreenlet
import hotCars
import dbUtils
import os
import sys
import argparse
from datetime import datetime

parser = argparse.ArgumentParser()
parser.add_argument('--LIVE', action='store_true') # Tweets are live

OUTPUT_DIR = os.environ['OPENSHIFT_DATA_DIR']
REPO_DIR = os.environ['OPENSHIFT_REPO_DIR']
SCRIPT_DIR = os.path.join(REPO_DIR, 'scripts')

class HotCarApp(RestartingGreenlet):

    def __init__(self, LIVE=False):
        RestartingGreenlet.__init__(self, LIVE=False)
        self.SLEEP = 40 # Run every 10 seconds
        self.LIVE = LIVE

    # Run forever
    def _run(self):

        while True:
            try:
                self.tick()
            except Exception as e:
                import traceback
                logFileName = os.path.join(OUTPUT_DIR, 'runHotCarApp.log')
                logFile = open(logFileName, 'a')
                logFile.write('HotCarApp: Caught Exception! %s\n'%str(e))
                tb = traceback.format_exc()
                logFile.write('Traceback:\n%s\n\n'%tb)
                logFile.close()
            gevent.sleep(self.SLEEP)
            raise RuntimeError('Hot car sabatoge!')

    def tick(self):

        logFileName = os.path.join(OUTPUT_DIR, 'runHotCarApp.log')

        with open(logFileName, 'a') as logFile:
            n = datetime.now()
            timeStr = n.strftime('%d-%B-%Y %H:%M:%S')
            msg = '*'*50 + '\n'
            msg += '%s Running Hot Car App\n'%timeStr
            logFile.write(msg)
            logFile.flush()

            # Run the tick
            runOnce(tweetLive=self.LIVE, log=logFile)

            logFile.close()

def runOnce(tweetLive=False, log=sys.stdout):
    # Establish connection with the database
    db = dbUtils.getDB()
    # Run one cycle of the hotcar app
    hotCars.tick(db, tweetLive=tweetLive, log=log)

if __name__ == '__main__':
    args = parser.parse_args()
    runOnce(tweetLive=args.LIVE)
