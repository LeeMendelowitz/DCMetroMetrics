#!/usr/bin/env python
"""
# This runs the ELESApp instance.

# This module can be executed directly for local testing
"""

if __name__ == "__main__":
    # Local Testing
    import test.setup

# python imports
import os
import sys
import subprocess
from datetime import datetime
import gevent
from gevent import Greenlet
import logging

# custom imports
from dcmetrometrics.common.globals import DATA_DIR, REPO_DIR, DATA_DIR
from dcmetrometrics.common.restartingGreenlet import RestartingGreenlet
from dcmetrometrics.eles.ELESApp import ELESApp
from dcmetrometrics.keys.keys import MetroEscalatorKeys, MetroElevatorKeys

OUTPUT_DIR = DATA_DIR
if OUTPUT_DIR is None:
    OUTPUT_DIR = os.getcwd()

if REPO_DIR is None:
    SCRIPT_DIR = os.getcwd()
else:
    SCRIPT_DIR = os.path.join(REPO_DIR, 'scripts')

###############################################################
# Log the ELES App to a file.
LOG_FILE_NAME = os.path.join(DATA_DIR, 'ELESApp.log')
fh = logging.FileHandler(LOG_FILE_NAME)
sh = logging.StreamHandler(sys.stderr)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
sh.setFormatter(formatter)

logger = logging.getLogger('ELESApp')
logger.addHandler(fh)
logger.addHandler(sh)
#################################################################

SLEEP = 30

##########################################
# Run the Twitter App as a Greenlet.
class App(RestartingGreenlet):

    def __init__(self, SLEEP=SLEEP, LIVE=False):
        RestartingGreenlet.__init__(self, SLEEP=SLEEP, LIVE=LIVE)
        self.LIVE = LIVE # Tweet only if Live
        self.SLEEP = SLEEP # Sleep time after each tick
        self.app = ELESApp(LIVE, MetroEscalatorKeys, MetroElevatorKeys)

    def _run(self):
        while True:
            try:
                self.app.tick()
            except Exception as e:
                import traceback
                logger.error('ElevatorApp caught Exception: %s\n'%(str(e)))
                tb = traceback.format_exc()
                logger.error('Traceback:\n%s\n\n'%tb)
            logger.info("sleeping...")
            gevent.sleep(self.SLEEP)


if __name__ == "__main__":
    print 'Running the ELES app locally....'
    a = App()
    a.start()
    a.join()
