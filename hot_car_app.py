"""
apps.hotCarApp

Define the HotCarApp as a restartingGreenlet.

This app will use the Twitter API to search for tweets about #wmata 
#hotcar's. These tweets and the hotcar data are stored in a database.
Tweet acknowledgements are posted to the @MetroHotCars twitter account.
"""

# TEST CODE
if __name__ == "__main__":
    import test.setup

import gevent
import os
import sys
from datetime import datetime

from dcmetrometrics.common.restarting_greenlet import RestartingGreenlet
from dcmetrometrics.common import db_globals
from dcmetrometrics.hotcars import hot_cars
from dcmetrometrics.common.globals import DATA_DIR, REPO_DIR, DATA_DIR

OUTPUT_DIR = DATA_DIR

###############################################################
# Log the HotCarApp App to a file.
import logging

LOG_FILE_NAME = os.path.join(DATA_DIR, 'HotCarApp.log')
fh = logging.FileHandler(LOG_FILE_NAME)
sh = logging.StreamHandler(sys.stderr)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
sh.setFormatter(formatter)

logger = logging.getLogger('HotCarApp')
logger.addHandler(fh)
logger.addHandler(sh)
#################################################################

class HotCarApp(RestartingGreenlet):

    def __init__(self, LIVE=False):

        db_globals.connect()

        RestartingGreenlet.__init__(self, LIVE=LIVE)
        self.SLEEP = 40 # Run every 10 seconds
        self.LIVE = LIVE

    # Run forever
    def _run(self):

        while True:

            try:

                hot_cars.tick(tweetLive = self.LIVE)

            except Exception as e:

                import traceback
                tb = traceback.format_exc()
                logger.error("HotCarApp Caught Error! %s\nTraceback:\n%s"%(str(e), tb))

            gevent.sleep(self.SLEEP)

        

if __name__ == '__main__':
    from time import sleep
    app = HotCarApp(LIVE = False)
    app.start()
    app.join()

