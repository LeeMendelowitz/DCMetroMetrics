from datetime import date, datetime, time
from collections import defaultdict

# Horrific Metro Encoding of Times in the Escalator/Elevator Incidents
# Here is an example:
# TimeOutOfService: 0343
# DateOutOfServ: '/Date(1358967600000+0000)/'
# DateUpdated:  '/Date(1358981288000+0000)/'

# TimeOutOfService is 03:43 (as in 24-hour time)
# The DateOutOfServ uses ms since the epoch.
# DateOutOfServ: datetime.datetime.fromtimestamp(1358967600) = datetime.datetime(2013, 1, 23, 14, 0)
# DateUpdated: datetime.datetime.fromtimestamp(1358981288) = datetime.datetime(2013, 1, 23, 17, 48, 8)
# Note: All DateOutOfServ always give hr=14, min=0. However, DateUpdate also gives resolution to the second!

def stripMetroDate(d):
    # example: /Date(1362202098000+0000)/
    # want to return integer: 1362202098
    assert(d[0:6]=='/Date(')
    return int(d[6:16])

# Parse a metro date. Return a date object
# Example: /Date(1362202098000+0000)/
def parseMetroDate(d):
    t = stripMetroDate(d)
    myDate = date.fromtimestamp(t)
    return myDate

# Parse a metro date. Return a datetime object
# Example: /Date(1362202098000+0000)/
def parseMetroDatetime(d):
    t = stripMetroDate(d)
    myDate = datetime.fromtimestamp(t)
    return myDate

def parseMetroTime(d):
    assert(len(d)==4)
    hr = int(d[0:2])
    m = int(d[2:])
    t = time(hour = hr, minute = m)
    return t

# Split an incident list by unit types (Escalators vs Elevators)
def splitIncidentsByUnitType(incList):
    elevators = [i for i in incList if i.isElevator()]
    escalators = [i for i in incList if i.isEscalator()]
    return (escalators, elevators)

#  Given two lists of incidents, identify those units that been added or removed
#  from incList1
def diffIncidentLists(incList1, incList2):

    idSet1 = set(i.UnitId for i in incList1)
    idSet2 = set(i.UnitId for i in incList2)

    unitToInc1 = dict( (i.UnitId, i) for i in incList1)
    unitToInc2 = dict( (i.UnitId, i) for i in incList2)

    if (len(unitToInc1) != len(incList1)):
        raise RuntimeError('There is a duplicate unit in incList1!')
    if (len(unitToInc2) != len(incList2)):
        raise RuntimeError('There is a duplicate unit in incList2!')

    unitsInBothReports = idSet1.intersection(idSet2)
    symptomDiffers = lambda myId: unitToInc1[myId].SymptomDescription != unitToInc2[myId].SymptomDescription
    statusChanged = [myId for myId in unitsInBothReports if symptomDiffers(myId)]

    newIncidents = [i for i in incList2 if i.UnitId not in idSet1]
    resolvedIncidents = [i for i in incList1 if i.UnitId not in idSet2]
    changedIncidents = [(unitToInc1[i], unitToInc2[i]) for i in statusChanged]

    result = { 'newIncidents' : newIncidents,
               'resolvedIncidents' : resolvedIncidents,
               'changedIncidents' : changedIncidents }

    return result

def collectIncidentsByStations(incList):
    d = defaultdict(list)
    for i in incList:
        d[i.StationCode].append(i)
    return d

def hasAttr(obj, attr):
    hasAttribute = True
    try:
        getattr(obj, attr)
    except AttributeError:
        hasAttribute = False
    return hasAttribute
