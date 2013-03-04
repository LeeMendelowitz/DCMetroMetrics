#! /usr/bin/env python

######################################
# Script to periodically make requests

import time
import makeEscalatorRequest
import datetime
import sys
from datetime import date, datetime, timedelta

runRequest = makeEscalatorRequest.run
requestHours = [6,11,16,21]
SLEEP_TIME = 60 # sleep for one minute
startDay = date.today()


# Generate report times
def reportTimeGen():
    requestHours = [6, 11, 16, 21]
    curInd = 0
    lastInd = len(requestHours) -1
    td = date.today()
    d = datetime(td.year, td.month, td.day) # midnight of the current day
    while True:
        hourOffset = requestHours[curInd]
        nt = d + timedelta(hours = hourOffset) # next report time
        if curInd < lastInd:
            curInd += 1
        else:
            curInd = 0
            d = d + timedelta(days = 1) # increment the day by 1
        yield nt



######################################
def run():
    rtg = reportTimeGen()
    rt = rtg.next()
    while True:
        t = datetime.now()
        if t > rt:
            timeStr = t.strftime('%d %b %Y %H:%M:%S')
            sys.stdout.write('Cur Time: %s\n'%timeStr)
            sys.stdout.flush()
            rt = rtg.next()
            runRequest()
        time.sleep(SLEEP_TIME)


if __name__ == '__main__':
    run()
