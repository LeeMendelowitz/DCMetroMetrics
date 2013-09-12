# Analysis for blog post response
# to this WMATA escalator performance
# new release:
# http://wmata.com/about_metro/news/PressReleaseDetail.cfm?ReleaseID=5575
import sys, os

# Modify system path to include dcmetrometrics module
_thisDir, _thisFile = os.path.split(os.path.abspath(__file__))
_parentDir = os.path.split(_thisDir)[0]
sys.path = [_parentDir] + sys.path

import test
from dcmetrometrics.common import dbGlobals
from dcmetrometrics.eles import dbUtils
dbg = dbGlobals.DBGlobals()
db = dbg.getDB()

def sout(msg):
    sys.stdout.write(msg +'\n')
    sys.stdout.flush()

def run1():

    sout('Computing escalator summaries...')
    escSummaries = dbUtils.getAllEscalatorSummaries(escalators=True)

    sout('Have %i escalator summaries'%len(escSummaries))

    numBreaks = sum(s['numBreaks'] for s in escSummaries.itervalues())
    absTime = max(s['absTime'] for s in escSummaries.itervalues())
    openTime = max(s['metroOpenTime'] for s in escSummaries.itervalues())

    sout('Number of breaks: %i'%numBreaks)
    sout('Absolute Time: %f days'%(absTime/3600.0/24.0))
    sout('Metro Open Time: %f days'%(openTime/3600.0/24.0))

    minutesPerBreak = openTime/60.0/float(numBreaks)
    sout('Minutes of metro open time per break: %f minutes'%minutesPerBreak)

    # TO DO:
    # Fill out a pandas DataFrame with information such as:
    # - meanTimeBetweenFailures (and rank)
    # - medianTimeBetweenFailures (and rank)
    # - longest Break (and rank)
    # - shortest Break (and rank)
    # - number of breaks (and rank)
    # - number of inspections (and rank)
    # - escalator meta data
    # - break days (number of metro days with an outage) and rank
    
    # Make a histogram of mean or median time between failures
    # Make a histogram of break days
    # Make a histogram of outage counts

    # Compute the percentage of outages which are attributed to
    # scheduled maintenance or inspections.

if __name__ == '__main__':
    run1() 
