#!/usr/bin/env python
"""
This is the main program. Running this module will cause
the twitter accounts to live tweet.

For testing purposes, run the test_app.py program, which
disables live tweeting.
"""

import imp
import os
import sys
import subprocess
import argparse
import copy


PY_DIR = os.environ['PYTHON_DIR']
REPO_DIR = os.environ['REPO_DIR']
SCRIPT_DIR = os.path.join(REPO_DIR, 'scripts')
DATA_DIR = os.environ['DATA_DIR']

# Import application modules
from ELESAppRunner import App as ELESAppRunner
# from elevatorApp import ElevatorApp
from hotCarApp import HotCarApp

# Import the web server and web page generator
import gevent
from gevent import monkey; monkey.patch_all() # Needed for bottle

HOT_CAR_TWEET_LIVE = 'HOT_CAR_TWEET_LIVE' in os.environ
ELES_TWEET_LIVE = 'ELES_TWEET_LIVE' in os.environ

def run():

   # Run MetroEscalators/MetroElevators twitter App
   elesApp = ELESAppRunner(LIVE = ELES_TWEET_LIVE)
   elesApp.start()

   # Run HotCar twitter app
   hotCarApplication = HotCarApp(LIVE = HOT_CAR_TWEET_LIVE)
   hotCarApplication.start()

   # Run forever
   while True:
       gevent.sleep(10)

if __name__ == '__main__':
   run()
