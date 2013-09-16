# Analysis for blog post response
# to this WMATA escalator performance
# new release:
# http://wmata.com/about_metro/news/PressReleaseDetail.cfm?ReleaseID=5575

# TO DO: 
#  - COMPUTE THE NUMBER OF OUTAGES ATTRIBUTED TO PREVENTATIVE MAINTENANCE.
#  - COMPUTE AVERAGE AVAILABILITY

import sys, os
import pandas
from collections import Counter
from datetime import date, time, datetime, timedelta

# Modify system path to include dcmetrometrics module
_thisDir, _thisFile = os.path.split(os.path.abspath(__file__))
_parentDir = os.path.split(_thisDir)[0]
sys.path = [_parentDir] + sys.path

import test
from dcmetrometrics.common import dbGlobals
from dcmetrometrics.common.metroTimes import tzutc, nytz, TimeRange
from dcmetrometrics.eles import dbUtils
dbg = dbGlobals.DBGlobals()
db = dbg.getDB()

def sout(msg):
    sys.stdout.write(msg +'\n')
    sys.stdout.flush()

def run1():

    endTime = datetime(2013, 9, 15, 12, tzinfo=nytz)

    sout('Computing escalator summaries...')
    escSummaries = dbUtils.getAllEscalatorSummaries(escalators=True, endTime = endTime)

    sout('Have %i escalator summaries'%len(escSummaries))

    numBreaks = sum(s['numBreaks'] for s in escSummaries.itervalues())
    absTime = max(s['absTime'] for s in escSummaries.itervalues())
    openTime = max(s['metroOpenTime'] for s in escSummaries.itervalues())

    firstStatus = db.escalator_statuses.find_one({}, sort=[('time', 1)])
    lastStatus = db.escalator_statuses.find_one({}, sort=[('time', -1)])
    firstStatusTime = firstStatus['time'].replace(tzinfo=tzutc)
    lastStatusTime = lastStatus['time'].replace(tzinfo=tzutc)

    # Summarize the break counts
    sout('*'*50)
    sout('Number of breaks: %i'%numBreaks)
    sout('First status time: %s'%str(firstStatusTime))
    sout('Last status time: %s'%str(lastStatusTime))
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

    # Print the average availability
    sout('*'*50)
    avgAvailability = df['availability'].mean()
    sout('Avg Availabiilty: %.3f%%'%(avgAvailability*100.0))

    # Determine how many outages include scheduled maintenance or inspections.
    allOutages = [o for ol in (v['outages'] for v in escSummaries.itervalues())\
                  for o in ol]
    numOutages = len(allOutages)
    numPlannedOutages = sum(1 for o in allOutages if o.is_planned)
    numBreakOutages = sum(1 for o in allOutages if o.is_break)
    numPlannedOutagesWhenOpen = sum(1 for o in allOutages if o.is_planned and o.metroOpenTime > 0.0)
    numOutagesWhenOpen = sum(1 for o in allOutages if o.metroOpenTime > 0.0)
    numBreakOutagesWhenOpen = sum(1 for o in allOutages if o.is_break and o.metroOpenTime > 0.0)
    sout('*'*50)
    sout('Number of outages: %i'%numOutages)
    sout('Number of planned outages: %i'%numPlannedOutages)
    sout('Number of break outages: %i'%numBreakOutages)
    sout('Fraction of planned outages: %.3f'%(100.0*float(numPlannedOutages)/numOutages))
    sout('\nWhen Metro is open:')
    sout('Number of outages: %i'%numOutagesWhenOpen)
    sout('Number of break outages: %i'%numBreakOutagesWhenOpen)
    sout('Number of planned outages: %i'%numPlannedOutagesWhenOpen)
    sout('Fraction of planned outages: %.3f'%\
          (100.0*float(numPlannedOutagesWhenOpen)/numOutagesWhenOpen))

    def hasTurnedOffSymptom(o):
        return any(s['symptom'] == 'TURNED OFF/WALKER' for s in o.statuses)
    numOutagesWithTurnedOff = sum(1 for o in allOutages if hasTurnedOffSymptom(o))
    symptomGen = (s['symptom'] for o in allOutages for s in o.statuses)
    symptomOutageCounts = Counter(symptomGen)

    def occursDuringTimeRange(o, startTime = time(7), endTime = time(21)):
        firstDay = o.timeRange.start.date()
        lastDay = o.timeRange.end.date()
        numDays = (lastDay - firstDay).days + 1
        days = [firstDay + timedelta(days=i) for i in range(numDays)]
        timeRanges = []
        for d in days:
            start = datetime.combine(d, startTime).replace(tzinfo=nytz)
            end = datetime.combine(d, endTime).replace(tzinfo=nytz)
            timeRanges.append(TimeRange(start, end))
        return any(tr.overlaps(o.timeRange) for tr in timeRanges)


    outagesBetween7And9 = [o for o in allOutages if occursDuringTimeRange(o)]
    numOutagesBetween7And9 = len(outagesBetween7And9)
    numBreaksBetween7And9 = sum(1 for o in outagesBetween7And9 if o.is_break)
    numPlannedOutagesBetween7And9 = sum(1 for o in outagesBetween7And9 if o.is_planned)
    sout('\nBetween 7 AM and 9 PM:')
    sout('Number of outages: %i'%numOutagesBetween7And9)
    sout('Number of break outages: %i'%numBreaksBetween7And9)
    sout('Number of planned outages: %i'%numPlannedOutagesBetween7And9)
    sout('Fraction of planned outages: %.3f'%\
          (100.0*float(numPlannedOutagesBetween7And9)/numOutagesBetween7And9))



    # Write the dataframe to disk
    outputPfx = 'escalatorOutageSummary'
    #df.to_excel('%s.xlsx'%outputPfx)
    df.to_csv('%s.csv'%outputPfx)
    df.to_html(open('%s.html'%outputPfx, 'w'))

    # Get the recently replaced escalators
    newEscalators = ['A03S01', 'A03S02', 'A03S03', 'C04X01', 'C04X02', 'C04X03']
    newEscalators = ['%sESCALATOR'%esc for esc in newEscalators]
    outputPfx = 'metroForwardEscalatorSummary'
    dfNewEscalators = df.ix[newEscalators].copy()
    columns = ['station_name', 'availability', 'availabilityRank', 'numBreaks', 'numBreaksRank', 'meanAbsTimeBetweenFailures', 'meanAbsTimeBetweenFailuresRank']
    dfNewEscalators = dfNewEscalators[columns]
    dfNewEscalators.availability = dfNewEscalators.availability * 100.0
    dfNewEscalators['meanDaysBetweenFailures'] = dfNewEscalators.meanAbsTimeBetweenFailures/3600.0/24.0
    dfNewEscalators['meanDaysBetweenFailuresRank'] = dfNewEscalators['meanAbsTimeBetweenFailuresRank']
    dfNewEscalators.to_csv('%s.csv'%outputPfx)
    dfNewEscalators.to_html(open('%s.html'%outputPfx, 'w'))

    return df


if __name__ == '__main__':
    run1() 
