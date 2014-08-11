"""
Miscellaneous utility functions
"""

import itertools
from operator import itemgetter, attrgetter

from ..common.metroTimes import isNaive

def get_one(cursor):
    """
    Get one item from the iterable.
    Return None if there is None.
    """
    try:
        return next(cursor)
    except StopIteration:
        return None

def get_some(cursor, N):
    """
    Get at most N items from the cursor, and return as a list
    """
    return [i for i in itertools.slice(cursor, N)]

def get_first_status_since(statusList, time):
    """
    Get the first status in the status list that starts after time.
    """
    statusList = sorted(statusList, key = attrgetter('time')) # in time ascending
    myRecs = (rec for rec in statusList if rec.time > time)
    return get_one(myRecs)

#############################################################  
def checkAllTimesNotNaive(statusList):
    for s in statusList:
        if isNaive(s.time):
            raise RuntimeError('Times cannot be naive')
        end_time = getattr(s, 'end_time', None)
        if end_time and isNaive(end_time):
            raise RuntimeError('Times cannot be naive')

#############################################################            
# Check that each status has a 'time' and 'end_time' defined
# and that the list is sorted            
def checkStatusListSane(statusList):
    lastTime = None
    for s in statusList:
        if not getattr(s, 'end_time', None):
            raise RuntimeError('Status missing end_time')
        if not getattr(s, 'time', None):
            raise RuntimeError('Status missing time')
        if s.time > s.end_time:
            raise RuntimeError('Status has bad starting/ending time')
        if lastTime and s.time < lastTime:
            raise RuntimeError('Status not sorted properly')
        lastTime = s.time

def yieldNothing():
    return 
    yield