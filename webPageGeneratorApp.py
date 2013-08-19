"""
Run an instance of the WebPageGenerator restartingGreenlet
for local testing.
"""

import dcmetrometrics.test.setup
from dcmetrometrics.web.WebPageGenerator import WebPageGenerator
print 'Running the webPageGenerator locally'
app = WebPageGenerator()
app.start()
app.join()
