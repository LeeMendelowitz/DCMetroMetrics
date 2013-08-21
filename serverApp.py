#!/usr/bin/env python
"""
Run a local instance of the DCMetroMetrics server
for local testing.
"""

# Local Testing
import test.setup
from gevent import monkey; monkey.patch_all()
from dcmetrometrics.web.server import Server

print 'Running the server locally....'
serverApp = Server()
serverApp.start()
serverApp.join()

