"""
Expose the server app for gunicorn in a testing environment
with the appropriate environmental variables.

To run:
gunicorn -w 4 -k gevent serve_gunicorn:app 
"""

# Local Testing
import test.setup
from gevent import monkey; monkey.patch_all()
from dcmetrometrics.web.server import app