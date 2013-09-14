# Analysis for blog post response
# to this WMATA escalator performance
# new release:
# http://wmata.com/about_metro/news/PressReleaseDetail.cfm?ReleaseID=5575

# TO DO: 
#  - COMPUTE THE NUMBER OF OUTAGES ATTRIBUTED TO PREVENTATIVE MAINTENANCE.
#  - COMPUTE AVERAGE AVAILABILITY

import sys, os
import pandas

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
    # Make a histogram of mean or median time between failures
    # Make a histogram of break days
    # Make a histogram of outage counts

    escSummaries = dict((s['unit_id'], s) for s in escSummaries.itervalues())
    df = pandas.DataFrame(escSummaries).T

    # Make a list of ranks to compute, (key, ascending)
    ranksToCompute = [('numBreaks', False),
                      ('numBrokenDays', False),
                      ('numInspections',False),
                      ('brokenTimePercentage', False),
                      ('availability', False),
                      ('meanAbsTimeBetweenFailures', False),
                      ('meanAbsTimeToRepair',False),
                      ('medianAbsTimeBetweenFailures', False),
                      ('medianAbsTimeToRepair', False),
                      ('maxAbsTimeBetweenFailures', False)]

    N = df.shape[0]
    for r, a in ranksToCompute:
        df['%sRank'%r] = df[r].rank(method='min',ascending=a)
        df['%sPercentile'%r] = df['%sRank'%r]/float(N)

    # Select and reorder the columns in a meaningful way
    cols = ['station_name', 'station_code', 'station_desc', 'esc_desc',
            'availability', 'availabilityRank',
            'brokenTimePercentage', 'brokenTimePercentageRank', 'brokenTimePercentagePercentile',
            'numBreaks', 'numBreaksRank', 'numBreaksPercentile',
            'numInspections', 'numInspectionsRank', 'numInspectionsPercentile',
            'numFixes',
            'meanAbsTimeBetweenFailures', 'meanAbsTimeBetweenFailuresRank',
            'meanAbsTimeBetweenFailuresPercentile',
            'meanAbsTimeToRepair', 'meanAbsTimeToRepairRank','meanAbsTimeToRepairPercentile',
            'maxAbsTimeBetweenFailures', 'maxAbsTimeBetweenFailuresRank',
            'maxAbsTimeBetweenFailuresPercentile',
            'numBrokenDays', 'numBrokenDaysRank', 'numBrokenDaysPercentile']
    df = df[cols]

    # Write the dataframe to disk
    outputPfx = 'escalatorOutageSummary'
    #df.to_excel('%s.xlsx'%outputPfx)
    df.to_csv('%s.csv'%outputPfx)
    df.to_html(open('%s.html'%outputPfx, 'w'))

    return df


if __name__ == '__main__':
    run1() 
