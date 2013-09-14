import setup
import test
from dcmetrometrics.common import dbGlobals
from dcmetrometrics.common.metroTimes import tzutc, TimeRange
import interval

from datetime import timedelta


dbg = dbGlobals.DBGlobals()
db = dbg.getDB()

MAX_TICK_DELTA = 3600
MAX_UPDATE_DELTA = 3600*5

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

def getDataOutageIntervals():
    """ 
    Return a list of TimeRanges for which escalator data was stale or unavailable
    """
    delayed = list(db.escalator_statuses.find({'tickDelta' : {"$gt" : MAX_TICK_DELTA}}))

    tickDeltaIntervals = []

    for s in delayed:
        endTime = s['time'].replace(tzinfo = tzutc)
        startTime = endTime - timedelta(seconds=s['tickDelta'])
        tickDeltaIntervals.append(TimeRange(startTime, endTime))
    
    tickDeltaIntervals = interval.union(tickDeltaIntervals)

    staleStatusIntervals = []
    allStatuses = db.escalator_statuses.find({}, sort=[('time',1)])
    last = None
    for s in allStatuses:
        if last is not None:
            delta = s['time'] - last['time']
            if delta.total_seconds() > MAX_UPDATE_DELTA:
                startTime = last['time'].replace(tzinfo=tzutc)
                endTime = s['time'].replace(tzinfo=tzutc)
                staleStatusIntervals.append(TimeRange(startTime, endTime))
        last = s
    staleStatusIntervals = interval.union(staleStatusIntervals)

    allIntervals = tickDeltaIntervals + staleStatusIntervals
    allIntervals = interval.union(allIntervals)
    return allIntervals

def adjustStatusListForOutages(statuses, outages):
    """
    Adjust a list of statuses sorted in ascending order by correcting for outages.
    If a status touches an outage interval, treat the escalator as "operational" during
    the data outage only if the symptom before the data outage and the symptom after the
    data outage are different.
    """
    pass
