# Utilities for determining opening/closing time
# of Metrorail system
##################################################

from datetime import time, date, datetime, timedelta

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

################################################
# Get the next time Metro opens after the time provided
def getNextOpenTime(t):
    today = t.date()

    def dateToOpen(d):
        wd = d.weekday()
        offset = wdToOpenOffset[wd]
        dt = datetime.combine(date=d,time=time()) + timedelta(hours = offset)
        return dt

    today = t.date()

    # Compute a few openeing times around today
    dayOffsets = range(-2,2)
    openingTimes = [dateToOpen(today+timedelta(days=offset)) for offset in dayOffsets]

    for ot in openingTimes:
        if ot > t:
            return ot
    raise RuntimeError('Something wrong in getNextOpenTime')

################################################
# Get the last time Metro opened before the time provided
def getLastOpenTime(t):
    today = t.date()

    def dateToOpen(d):
        wd = d.weekday()
        offset = wdToOpenOffset[wd]
        dt = datetime.combine(date=d,time=time()) + timedelta(hours = offset)
        return dt

    today = t.date()

    # Compute a few openeing times around today
    dayOffsets = range(-2,2)
    openingTimes = [dateToOpen(today+timedelta(days=offset)) for offset in dayOffsets]

    for ot in openingTimes[::-1]:
        if ot <= t:
            return ot
    raise RuntimeError('Something wrong in getLastOpenTime')

################################################
def getNextCloseTime(t):

    def dateToClose(d):
        wd = d.weekday()
        offset = wdToCloseOffset[wd]
        dt = datetime.combine(date=d,time=time()) + timedelta(hours = offset)
        return dt

    today = t.date()

    # Compute a few closing times around today
    dayOffsets = range(-1,2)
    closingTimes = [dateToClose(today+timedelta(days=offset)) for offset in dayOffsets]

    for ct in closingTimes:
        if ct > t:
            return ct
    raise RuntimeError('Something wrong in getNextCloseTime')

################################################
def getLastCloseTime(t):

    def dateToClose(d):
        wd = d.weekday()
        offset = wdToCloseOffset[wd]
        dt = datetime.combine(date=d,time=time()) + timedelta(hours = offset)
        return dt

    today = t.date()

    # Compute a few closing times around today
    dayOffsets = range(-2,2)
    closingTimes = [dateToClose(today+timedelta(days=offset)) for offset in dayOffsets]

    for ct in closingTimes[::-1]:
        if ct <= t:
            return ct
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
        t = self.start
        secOpen = 0.0
        while t < self.end:
            ts = getNextOpenTime(t) if not metroIsOpen(t) else t
            te = getNextCloseTime(ts)
            assert(te > ts)
            if ts > self.end:
                break
            te = min(te, self.end)
            assert(te > ts)
            secOpen += (te - ts).total_seconds()
            t = te
        return secOpen

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
