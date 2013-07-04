# Utilities for determining opening/closing time
# of Metrorail system
##################################################

from datetime import time, date, datetime, timedelta
combine = datetime.combine

# Sunday: Opens at 7 AM
# Monday - Friday: Opens at 5 AM
# Saturday: Opens at 7 AM
# index 0 is monday
wdToOpenOffset = [5, 5, 5, 5, 5, 7, 7]

# Sunday: Closes at 12 AM
# Monday - Thurs: Closes at 12 AM
# Friday: Closes at 3 AM next day
# Saturday: Closes at 3 AM next day
# index 0 is monday
wdToCloseOffset = [24, 24, 24, 24, 27, 27, 24]

wdToOpenHours = [closeHour - openHour for openHour, closeHour in zip(wdToOpenOffset, wdToCloseOffset)]

def dateToOpen(d):
    wd = d.weekday()
    offset = wdToOpenOffset[wd]
    dt = combine(date=d,time=time()) + timedelta(hours = offset)
    return dt

def dateToClose(d):
    wd = d.weekday()
    offset = wdToCloseOffset[wd]
    dt = combine(date=d,time=time()) + timedelta(hours = offset)
    return dt

def dateToOpenHours(d):
    wd = d.weekday()
    return timedelta(hours=wdToOpenHours[wd])

#######################################################
# Get the next time Metro opens after the time provided
def getNextOpenTime(t):
    today = t.date()
    o = dateToOpen(today)
    # Try today's opening time
    if o > t:
        return o
    # Try tomorrow's opening time
    o = dateToOpen(today + timedelta(days=1))
    if o > t:
        return o
    raise RuntimeError('Something wrong in getNextOpenTime')

#########################################################
# Get the last time Metro opened (less than or equal to the current time)
def getLastOpenTime(t):
    today = t.date()
    o = dateToOpen(today)
    # Try today's opening time
    if o <= t:
        return o
    # Try yesterday's opening time
    o = dateToOpen(today + timedelta(days=-1))
    if o <= t:
        return o
    raise RuntimeError('Something wrong in getLastOpenTime')

################################################
# Get the next close time (greater than the current time)
def getNextCloseTime(t):
    today = t.date()
    # Try yesterday's closing time (which may be today)
    c = dateToClose(today+timedelta(days=-1))
    if c > t:
        return c
    # Try today's closing time
    c = dateToClose(today)
    if c > t:
        return c
    raise RuntimeError('Something wrong in getNextCloseTime')

################################################
# Get the last close time (less than or equal to current time)
# Note: The less than or equal is critical to the MetroIsOpen function
def getLastCloseTime(t):
    today = t.date()

    # Compute a few closing times around today
    # This is tricky:
    # If it is 2 AM Saturday, the last close time was Thursday's closing at 12 AM Friday.
    # If it is 4 AM Saturday, the last close time was Friday's closing at 3 AM Saturday.

    # Try yesterday's closing time (which may be today)
    c = dateToClose(today + timedelta(days=-1))
    if c <= t:
        return c
    # Try yester-yesterday's closing time
    c = dateToClose(today + timedelta(days=-2))
    if c <= t:
        return c
    raise RuntimeError('Something wrong in getLastCloseTime')

################################################
def metroIsOpen(t):
    lastClose = getLastCloseTime(t)
    lastOpen = getLastOpenTime(t)
    return (lastOpen > lastClose)

class TimeRange(object):
    def __init__(self, start, end):
        if start > end:
            raise RuntimeError('Invalid time range!')
        self.start = start
        self.end = end

    def absTime(self):
        return (self.end - self.start).total_seconds()

    # Get the amount of seconds in time range for which
    # Metrorail was open
    def metroOpenTime(self):
        start = self.start
        end = self.end
        t = start
        secOpen = 0.0
        while t < end:
            ts = getNextOpenTime(t) if not metroIsOpen(t) else t
            te = getNextCloseTime(ts)
            assert(te > ts)
            if ts > end:
                break
            te = min(te, end)
            assert(te > ts)
            secOpen += (te - ts).total_seconds()
            t = te
        return secOpen

#    def metroOpenTime2(self):
#        start = self.start
#        end = self.end
#        d1 = start.date()
#        d2 = end.date()
#        openTimeBeforeStart = getLastOpenTime(start)
#        openTimeBeforeEnd = getLastOpenTime(end)
#        numDays = (d1-d2).days
#
#        isFullDay = lambda d: (dateToOpen(d) >= start) and (dateToClose(d) <= end)
#
#        # Collect the full days in between the start and end time
#        dateGen = (d1 + timedelta(days=delta) for delta in xrange(numDays+1))
#        fullDay = (d for d in dategen if isFullday(d))
#
#        # Count the hours from the full days (as a timedelta instance)
#        fullDayHours = sum((dateToOpenHours(d) for d in fullDay), timedelta(hours=0))
#
#        # Compute hours for the first day
#        firstDayTime = None
#        if not isFullDay(d1):
#            day1start = start if metroIsOpen(start) else getNextStartTime(start)
#            day1end = min(getNextCloseTime(day1start), end)
#            firstDayTime = day1end - day1start if day1end > day1start else timedelta(0.0)
#
#        # Compute hours for the last day
#        lastDayIsDifferent = (d1 != d2) and (openTimeBeforeStart != openTimeBeforeEnd)
#        if (d2 > d1) and not is 

def secondsToDHM(seconds):
    secondsPerDay = 24 * 3600
    numDays = int(seconds/secondsPerDay)
    rem = seconds - numDays*secondsPerDay
    d = datetime(2000,1,1) + timedelta(seconds=rem)
    dstr = d.strftime('%Hh %Mm')
    if numDays > 0:
        timeStr = '%id %s'%(numDays, dstr)
    else:
        timeStr = dstr
    return timeStr

def secondsToHMS(seconds):
    secondsPerDay = 24 * 3600
    numDays = int(seconds/secondsPerDay)
    rem = seconds - numDays*secondsPerDay
    d = datetime(2000,1,1) + timedelta(seconds=rem)
    hours = numDays*24 + d.hour
    minutes = d.minute
    seconds = d.second
    timeStr = '%ih %im %is'%(hours,minutes,seconds)
    return timeStr
