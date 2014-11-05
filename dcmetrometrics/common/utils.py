from datetime import date, datetime, time, timedelta
from collections import defaultdict
import sys

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

def readEscalatorTsv(fname):
    fin = open(fname)
    fieldNames = ['unit_id', 'station_code', 'station_name', 
                  'station_desc', 'esc_desc']
    escData = []
    for l in fin:
        fields = l.strip().split('\t')
        assert(len(fields) == len(fieldNames))
        d = dict((k,v.strip()) for k,v in zip(fieldNames,fields))
        escData.append(d)
    fin.close()
    return escData

################################################################
# Convert a units file (with fields station_name, unit_id, and esc)
# to a TSV file (with fields unit_id, station_code, station_name, station_desc,
# esc_desc)
def unitsFileToTsv(fname, fout=sys.stdout):
    fin = open(fname)
    fieldNames = ['station_name', 'unit_id', 'desc']
    escData = []

    lines = (l.strip() for l in fin)
    lines = (l for l in lines if l)
    for l in lines:
        fields = l.split('\t')
        assert(len(fields) == len(fieldNames))
        d = dict((k,v.strip()) for k,v in zip(fieldNames,fields))
        escData.append(d)
    fin.close()
    
    def makeD(d):
        unit = d['unit_id']
        station_code = unit[0:3]
        station_name = d['station_name']
        station_desc = ''
        esc_desc = d['desc']
        if ',' in station_name:
            station_name, station_desc = station_name.split(',', 1)
        newd = {'unit_id' : d['unit_id'],
                'station_name' : station_name,
                'station_code' : station_code,
                'station_desc' : station_desc,
                'esc_desc' : esc_desc }
        return newd

    # Transform the esc data
    escData = [makeD(d) for d in escData]

    fieldNames = ['unit_id', 'station_code', 'station_name', 
                  'station_desc', 'esc_desc']
    for d in escData:
        fields = [d[k] for k in fieldNames]
        fout.write('\t'.join(fields) + '\n')

import os, errno
def mkdir_p(path):
    """
    Recursively make the directory pointed to by path.
    """
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise

def gen_days(s, e):
    """Generate days between start_day s and end_day e (exclusive)"""
    d = s
    while d < e:
        yield d
        d = d + timedelta(days = 1)
