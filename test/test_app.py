#!/usr/bin/env python
"""
Test the app.py in the repo directory
This includes the hotcars app, and the escalator app
"""

import os, sys, subprocess, imp

# Setup environmental variables and fix the system path
import setup

from gevent import monkey; monkey.patch_all()
appPath = os.path.join(setup.HOME_DIR, 'app.py')
appModule = imp.load_source('app', appPath)
appModule.run()
