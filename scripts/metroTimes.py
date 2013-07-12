# Utilities for determining opening/closing time
# of Metrorail system
# TODO: Make this module correct for daylights saving time.

##################################################
from datetime import time, date, datetime, timedelta
from dateutil.tz import tzlocal, tzutc
from dateutil import zoneinfo
nytz = zoneinfo.gettz("America/New_York")
tzutc = tzutc()
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
    dt = dt.replace(tzinfo=nytz)
    return dt

def dateToClose(d):
    wd = d.weekday()
    offset = wdToCloseOffset[wd]
    dt = combine(date=d,time=time()) + timedelta(hours = offset)
    dt = dt.replace(tzinfo=nytz)
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

        if any(isNaive(t) for t in (start, end)):
            raise RuntimeError('TimeRange: start and end cannot be naive')
        if start > end:
            raise RuntimeError('Invalid time range!')
        self.start = toLocalTime(start)
        self.end = toLocalTime(end)

    def absTime(self):
        return (self.end - self.start).total_seconds()

    def metroOpenTime(self):
        start = self.start
        end  = self.end
        secOpen = 0.0

        # Trick: Think of a "Metro Day" as the time range between conesecutive openings.
        # Each time the metro opens, it's a new day.
        #
        # |------|------|------|------|-----|-----|
        # Open   Close  O      C      O     C     O
        # <------------>|<----------->|<--------->|
        #    Day 0           Day 1        Day 2

        firstDayOpenTime = getLastOpenTime(start)
        firstDay = firstDayOpenTime.date()
        firstDayCloseTime = getNextCloseTime(firstDayOpenTime)
        lastDayOpenTime = getLastOpenTime(end)
        lastDay = lastDayOpenTime.date()

        # First consider the case where the time range is within one metro day
        #  |--------|---------|
        #  O        C         O
        #     |---------|
        #     S         E
        if firstDay == lastDay:
            startTime = start
            endTime = min(end, firstDayCloseTime)
            totalSeconds = (endTime - startTime).total_seconds() if endTime > startTime\
                           else 0.0
            return totalSeconds

        lastDayCloseTime = getNextCloseTime(lastDayOpenTime)
        lastDayEnd = min(lastDayCloseTime, end)

        # In the other case, the time range spans multiple metro days.
        # Add the contributions from the first day, the last day, and interior days (if any)
        firstDaySeconds = (firstDayCloseTime - start).total_seconds() if start < firstDayCloseTime\
                          else 0.0
        lastDaySeconds  = (min(lastDayCloseTime, end) - lastDayOpenTime).total_seconds()
        assert(lastDaySeconds >= 0.0)

        numDays = (lastDay - firstDay).days
        assert(numDays >= 1)
        interiorDays = (firstDay + timedelta(i) for i in range(1, numDays)) 
        interiorHours = sum(wdToOpenHours[d.weekday()] for d in interiorDays)
        interiorSeconds = interiorHours *3600.0
        metroOpenSeconds = firstDaySeconds + lastDaySeconds + interiorSeconds
        return metroOpenSeconds

    ###################################################
    # Get the amount of seconds in time range for which
    # Metrorail was open
    def metroOpenTime_OLD(self):
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

##################################################
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

##################################################
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

##################################################
# Convert UTC datetime to local datetime.
# We use New York Time
# If utcDateTime is naive, treat timezone as UTC
def UTCToLocalTime(utcDateTime):
    from_zone = tzutc
    to_zone = nytz
    if utcDateTime.tzinfo is None:
        utcDateTime = utcDateTime.replace(tzinfo=from_zone)
    localdt = utcDateTime.astimezone(to_zone)
    return localdt

##################################################
# Convert local dateTime to UTC dateTime
# If localDateTime is naive, treat timezone as NY
def localToUTCTime(localDateTime):
    from_zone = nytz
    to_zone = tzutc
    if localDateTime.tzinfo is None:
        localDateTime = localDateTime.replace(tzinfo=from_zone)
    utcDt = localDateTime.astimezone(to_zone)
    return utcDt

#################################################
# Convert a non-naive datetime to UTC
def toUtc(dt):
    if isNaive(dt):
        raise RuntimeError('toUtc: datetime cannot be naive')
    dt = dt.astimezone(tzutc)
    return dt

#################################################
# Convert a non-naive datetime to NY time
def toLocalTime(dt):
    if isNaive(dt):
        raise RuntimeError('toLocalTime: datetime cannot be naive')
    dt = dt.astimezone(nytz)
    return dt

#################################################
def makeNaive(dt):
    return dt.replace(tzinfo=None)

#################################################
def isNaive(dt):
    return dt.tzinfo is None

#################################################
def utcnow():
    return datetime.utcnow().replace(tzinfo=tzutc)
