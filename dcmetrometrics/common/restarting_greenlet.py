"""
common.restartingGreenlet

Extend the gevent Greenlet class so that the Greenlet restarts whenever it finishes.
"""

import sys
from gevent import Greenlet, sleep
from datetime import datetime

def makeNewGreenlet(g):
    args = g.rsargs
    kwargs = g.rskwargs
    newg = g.__class__(*args, **kwargs)
    t = type(newg)
    gid = str(newg)
    dateStr = str(datetime.now())
    sys.stderr.write('%s: Making new greenlet %s of type %s\n'%(dateStr, gid, str(t)))

    # Impose a short sleep. This is to prevent a buggy RestartingGreenlet 
    # from perpetually throwing an exception and continually restarting
    # TO DO: Consider a max restarts parameter
    sleep(1)
    return newg

class RestartingGreenlet(Greenlet):

    def __init__(self, *args, **kwargs):
        Greenlet.__init__(self)

        # Save the constructer arguments
        # so we can recreate the Greenlet
        self.rsargs = args
        self.rskwargs = kwargs

        # Set up this Greenlet to use the restarter
        self.link(self.restart)

    @staticmethod
    def restart(g):
        newg = makeNewGreenlet(g)
        newg.start()
