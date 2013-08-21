#!/usr/bin/env python
"""
Generate all web pages.
This script works for both an OpenShift deployment 
and for local testing.
"""

import sys, os
import utils

if not utils.isOpenshiftEnv():
    print 'This does not appear to be an Openshift Environment.'
    utils.fixSysPath()
    import test.setup # Fixes the system path so we can import dcmetrometrics.
else:
    print 'This appears to be an Openshift Environment.'

print '*'*50

from dcmetrometrics.web import WebPageGenerator
WebPageGenerator.updateAllPages()


