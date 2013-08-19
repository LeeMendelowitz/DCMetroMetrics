#!/usr/bin/env python
"""
Test the app.py in the repo directory
This includes the web server, the hotcars app, and the
escalator app
"""

import os
import sys
import subprocess
import imp

# Setup environmental variables
import dcmetrometrics.test.setup

from gevent import monkey; monkey.patch_all()

# Run the application
cwd = os.getcwd()
REPO_DIR = os.environ['OPENSHIFT_REPO_DIR']
appPath = os.path.join(REPO_DIR, 'app.py')
appModule = imp.load_source('app', appPath)
appModule.run(LIVE=False)
