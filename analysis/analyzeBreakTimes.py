# Analysis of the time of day when
# breaks are reported
import pandas
from datetime import datetime, timedelta, date
from collections import Counter, defaultdict

import dcmetrometrics.test.setup
from dcmetrometrics.common import metroTimes, dbGlobals
from dcmetrometrics.common.metroTimes import nytz, toLocalTime
from dcmetrometrics.eles import dbUtils
from dcmetrometrics.eles.StatusGroup import StatusGroup

MAX_TICK_DELTA = 3600

dbg = dbGlobals.DBGlobals()
db = dbg.getDB()

def getAllBreaks():
    
    escIds = dbg.getEscalatorIds()
    breaks = []
    for escId in escIds:
        statuses = dbUtils.getEscalatorStatuses(escId)
        # Sort in ascending order
        statuses = statuses[::-1]
        sg = StatusGroup(statuses)
        breaks.extend(sg.breakStatuses)
    return breaks

def getFilteredBreaks():
    breaks = getAllBreaks()

    # Do not include days where a data outage occurred
    daysToIgnore = getDataOutageDays()
    daysToIgnore.add(date(2013,6,1)) # This is the first day when data was collected
    daysToIgnore.add(date(2013,7,4)) # 4th of July ran on a different schedule

    breaks = [d for d in breaks if d['time'].date() not in daysToIgnore]
    assert(all(b['tickDelta'] < MAX_TICK_DELTA for b in breaks))
    return breaks

def summarizeBreaks(breaks):
    dates = [b['time'].date() for b in breaks]

    dateCount = Counter(dates)
    weekdayBreakCount = Counter(d.weekday() for d in dates)
    dateSet = set(dates)
    weekdayCount = Counter(d.weekday() for d in dateSet)

    print '*'*50
    print 'Date Counts:'
    dates = sorted(dateCount.keys())
    for d in dates:
        print d,dateCount[d]

    print '*'*50
    print 'Weekday Counts:'
    for w in sorted(weekdayBreakCount.keys()):
        print w, weekdayCount[w], weekdayBreakCount[w], float(weekdayBreakCount[w])/weekdayCount[w]

def writeBreakCsv(fname='breaks.csv'):
    breaks = getFilteredBreaks()

    # Do not include days where a data outage occurred
    daysToIgnore = getDataOutageDays()
    daysToIgnore.add(date(2013,6,1)) # This is the first day when data was collected
    daysToIgnore.add(date(2013,7,4)) # 4th of July ran on a different schedule

    breaks = [d for d in breaks if d['time'].date() not in daysToIgnore]

    # Turn into a pandas object
    breakGen = ((b['unit_id'], b['time'].isoformat()) for b in breaks)
    dt = pandas.DataFrame(list(breakGen), columns=['escalator', 'breaktime'])
    dt.to_csv(fname, index=False)
    return dt

def getDataOutageDays():
    """
    Return days which have been impacted by a data outage
    """
    delayed = list(db.escalator_statuses.find({'tickDelta' : {"$gt" : MAX_TICK_DELTA}}))
    daysWithDelay = set()
    # Get the days impacted by a data outage
    for d in delayed:
        endTime = d['time']
        startTime = endTime - timedelta(seconds=d['tickDelta'])
        startDay = startTime.date()
        endDay = endTime.date()
#        print 'startDay: %s endDay: %s'%(str(startDay), str(endDay))
        numDays = (endDay - startDay).days
        days = (startDay + timedelta(days=i) for i in xrange(numDays+1))
        daysWithDelay.update(days)
    return daysWithDelay

#################################
def getOutageStartDurations(fname='outageStartToDuration.csv'):
    escStatusDict = dbg.getAllEscalatorStatuses()
    sgs = [StatusGroup(sl) for sl in escStatusDict.itervalues()]
    
    # Get all escalator outages which are not still ongoing (i.e. they have been resolved)
    outages = [o for sg in sgs for o in sg.outageStatuses]
    outages = [o for o in outages if not o.is_active]
    print 'Found %i outages'%len(outages)

    # Filter out any outages that included an inspection or rehabilitation or off status.
    # These are pure breaks.
    breaks = [o for o in outages if not (o.is_off or o.is_rehab or o.is_inspection) and o.is_break]
    print 'Found %i breaks'%len(breaks)

    # For each break, determine the duration. Write to csv file.
    data = []
    for b in breaks:
        startTime = toLocalTime(b.startTime)
        endTime = toLocalTime(b.endTime)
        day = startTime.weekday()
        hour = startTime.hour
        duration = (endTime - startTime).total_seconds()
        dayStart = datetime(startTime.year, startTime.month, startTime.day, tzinfo = startTime.tzinfo)
        dayseconds = (startTime - dayStart).total_seconds()
        d = [startTime.isoformat(),
             day,
             hour,
             dayseconds,
             duration]
        data.append(d)
    dt = pandas.DataFrame(data, columns=['time', 'day', 'hour', 'dayseconds', 'duration'])
    dt.to_csv(fname, index=False)

    catToOutages = defaultdict(list)
    for o in outages:
        key = tuple(sorted(list(o.categories)))
        catToOutages[key].append(o)

    ret = {'breaks' : breaks,
           'catToOutages' : catToOutages}
    return ret
