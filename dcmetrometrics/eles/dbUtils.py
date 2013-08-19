"""
eles.dbUtils

Utilities for pulling or writing escalator/elevator data
to the MongoDB collections.
"""

# python imports
import pymongo
import sys
import os
from collections import defaultdict, Counter
from datetime import datetime, time, date, timedelta
from operator import itemgetter
import copy
import gevent


# custom imports
from ..common import dbGlobals, stations
from ..common.metroTimes import TimeRange, utcnow, isNaive, toUtc, tzutc
from .defs import symptomToCategory, OPERATIONAL_CODE as OP_CODE
from .StatusGroup import StatusGroup, _checkAllTimesNotNaive

invDict = lambda d: dict((v,k) for k,v in d.iteritems())

##########################################
# Get one item from the cursor. Return None if there is no item.
def getOne(cursor):
    try:
        res = next(cursor)
        return res
    except StopIteration:
        return None

######################################################################
# Get at most N items from the cursor. Return a generator over the N items.
def _getSome(cursor, N):
    for i, item in enumerate(cursor):
        if i >= N:
            break
        yield item

# Get at most N items from the cursor. Return a list of items
def getSome(cursor, N):
    return [item for item in _getSome(cursor, N)]

#######################################################################
def getFirstStatusSince(statusList, time):
    statusList = sorted(statusList, key = itemgetter('time')) # in time ascending
    myRecs = (rec for rec in statusList if rec['time'] > time)
    return getOne(myRecs)

######################################################################
def updateAppState(db, lastRunTime = None, nextDailyStatusTime = None):
    update = {}
    if lastRunTime is not None:
        update['lastRunTime'] = lastRunTime
    if nextDailyStatsTime is not None:
        update['nextDailyStatsTime'] = nextDailyStatusTime
    if not update:
        return
    update = {'$set' : update}
    db.app_state.update({'_id' : 1}, update, upsert=True)

########################################
# Initialize the escalator database with entries, and
# initialize the escalator_statuses database with default
# OPERATIONAL entries
def initializeEscalators(db, escDataList, curTime):
    for d in escDataList:
        addUnit(db, curTime, d)

########################################
# Add escalator to the database if it does not exist already.
# Note: This will not modify the escalator attributes if a document
# with a matching unit_id already exists
def addUnit(db, curTime, data):

    requiredKeys = ['unit_id', 'station_code', 'station_name', 'station_desc','esc_desc', 'unit_type']
    if not all(r in data for r in requiredKeys):
        raise RuntimeError('addUnit: data missing a required key. Has keys %s'%(', '.join(data.keys())))

    unitCollection = db['escalators']
    statusCollection = db['escalator_statuses']

    # See if this escalator already exists in the database
    unitCollection.ensure_index('unit_id')
    query = {'unit_id' : data['unit_id']}
    count = unitCollection.find(query).count()
    if count not in (0,1):
        raise RuntimeError("Unit Collections has multiple entries for %s"%data['unit_id'])

    # Add the unit to the unitCollection if necessary
    escId = None
    if count == 0:
        escId = unitCollection.insert(data)
    else:
        escId = unitCollection.find_one(query)['_id']
    assert(escId)

    # Add a new entry to the escalator_statuses collection if necessary
    statusCount = statusCollection.find({'escalator_id' : escId}).count()
    if statusCount == 0:
        doc = {'escalator_id' : escId,
               'time' : curTime - timedelta(seconds=1),
               'tickDelta' : 0,
               'symptom_code' : OP_CODE}
        statusCollection.insert(doc)

######################################################################
def addSymptomCode(db, symptom_code, symptom_desc):
    query = {'_id' : int(symptom_code)}
    count = db.symptom_codes.find(query).count()
    if count == 0:
        d = {'_id' : int(symptom_code),
             'symptom_desc': symptom_desc}
        db.symptom_codes.insert(d)

###############################################################
# Update the database from incident data
# This will add any new escalators or symptom codes that
# have not yet been seen to the appropriate collection
def updateDBFromIncidentData(db, inc, curTime):

    # Add the escalator to the database
    doc = { 'unit_id' : inc['UnitId'],
          'station_code' : inc['StationCode'],
          'station_name' : inc['StationName'],
          'esc_desc' : inc['LocationDescription'],
          'station_desc' : inc['StationDesc'],
          'unit_type' : inc['UnitType']
    }
    addUnit(db, curTime, doc)

    # Add the symptom code to the database
    addSymptomCode(db, inc.SymptomCode, inc.SymptomDescription)

##########################################################
# Retrieve information about the latest statuses for all escalators
# Return a dictionary (key=escalator_id, value=status_dict)
# status_dict is dictionary returned by getKeyStatuses
# If both 'escalators' and 'elevators' are True or False, return
# all of the statuses
#
# NOTE: This function can probably be improved by using MongoDB
#       group or aggregate features, instead of retrieving escalator/elevators
#       statuses escalator by escalator
def getLatestStatuses(escalators=False, elevators=False, dbg=None):
   
    if dbg is None:
        dbg = dbGlobals.DBGlobals()
    db = dbg.getDB()

    if escalators and not elevators:
        esc_ids = dbg.getEscalatorIds()
    elif elevators and not escalators:
        esc_ids = dbg.getElevatorIds()
    else:
        # Get both escalators and elevators
        esc_ids = dbg.getUnitIds()

    db.escalator_statuses.ensure_index([('escalator_id', pymongo.ASCENDING),
                                        ('time', pymongo.DESCENDING)])
    escToStatuses = {}

    for esc_id in esc_ids:
        # Find latest 1000 statuses for this escalator
        sort_params = [('time', pymongo.DESCENDING)]
        statuses = getEscalatorStatuses(esc_id, dbg=dbg)
        keyStatuses = getKeyStatuses(statuses, dbg=dbg)
        keyStatuses['statuses'] = statuses
        escToStatuses[esc_id] = keyStatuses

    return escToStatuses

###############################################
# Add attributes to each escalator_status doc
# in a sorted list of escalator docs for a single escalator/elevator.
# To properly set end_time, docs must be sorted
# in time descending order before calling this function.
# - end_time: time when this status is replaced by a more recent status.
# - symptom: symptom description (string)
# - symptomCategory: symptom category (string)
# - unit_id: full unit id (eg 'A03N01ESCALATOR')
# - station_name: from escalators collection
# - station_desc: from escalators collection
# - station_code: from escalators collection
# - esc_desc: from escalators collection
def addStatusAttr(statusList, dbg=None):

    if not statusList:
        return

    if dbg is None:
        dbg = dbGlobals.DBGlobals()

    _checkAllTimesNotNaive(statusList)

    # Check that these statuses concern a single escalator
    escids = set(s['escalator_id'] for s in statusList)
    if not len(escids)==1:
        raise RuntimeError('makeFullStatuses: received status list for multiple escalators!')
    escId = escids.pop()

    # Get the escalator data for this escalator
    escData = dbg.escIdToEscData.get(escId, None)
    if escData is None:
        raise RuntimeError('makeFullStatuses: Missing escalator data for escalator id: %s'%str(escId))

    lastTime = None
    lastIndex = len(statusList)-1
    escDataKeys = ['unit_id', 'station_name', 'station_desc', 'station_code', 'esc_desc']
    for i, d in enumerate(statusList):
        # Add end_time
        if i != lastIndex:
            statusList[i+1]['end_time'] = d['time']
        if i > 0 and d['time'] > lastTime:
            raise RuntimeError('makeFullStatuses: escalator statuses not properly sorted!')
        # Add symptom fields
        symp = dbg.symptomCodeToSymptom[d['symptom_code']]
        d['symptom'] = symp
        d['symptomCategory'] = symptomToCategory[symp]
        # Add escalator data fields 
        d.update((k, escData[k]) for k in escDataKeys)
        lastTime = d['time']

###############################################
# From a list of statuses, select key statuses
# -lastFix: The oldest operational status which follows the most recent break
# -lastBreak: The most recent broken status which has been fixed.
# -lastInspection: The last inspection status
# -lastOp: The most recent operational status
# -lastStatus: The most recent status
# Note: If there is a transition between broken states, such as :
# ... OPERATIONAL -> CALLBACK/REPAIR -> MINOR REPAIR -> OPERATIONAL,
# then the lastBreak status is that of the CALLBACK/REPAIR, since it is the
# first broken status in the stretch of brokeness.
def getKeyStatuses(statuses,dbg=None):

    _checkAllTimesNotNaive(statuses)

    # Check that these statuses concern a single escalator
    escids = set(s['escalator_id'] for s in statuses)
    if len(escids) > 1:
        raise RuntimeError('getKeyStatuses: received status list for multiple escalators!')

    # Sort statuses by time in descending order
    statusesRevCron = sorted(statuses, key = itemgetter('time'), reverse=True)
    statusesCron = statusesRevCron[::-1]
    statuses = statusesRevCron

    # Add additional attributes to all statuses
    addStatusAttr(statuses, dbg=dbg)

    # Organize the operational statuses and breaks.
    # Associate each operational status with the next break which follows it
    # Associate each break with the next operational status which follows it
    ops = [rec for rec in statuses if rec['symptomCategory'] == 'ON']
    opTimes = [rec['time'] for rec in ops]
    breaks = [rec for rec in statuses if rec['symptomCategory'] == 'BROKEN']
    breakTimes = [rec['time'] for rec in breaks]

    breakTimeToFix = {}
    opTimeToNextBreak = {}
    for bt in breakTimes:
        breakTimeToFix[bt] = getFirstStatusSince(ops, bt)
    for opTime in opTimes:
        opTimeToNextBreak[opTime] = getFirstStatusSince(breaks, opTime)

    lastOp = ops[0] if ops else None
    lastStatus = statuses[0] if statuses else None

    def getStatus(timeToStatusDict):
        keys = sorted(timeToStatusDict.keys(), reverse=True)
        retVal = None
        for k in keys:
            retVal = timeToStatusDict[k]
            if retVal is not None:
                return retVal
        return retVal

    # Get the most recent break
    lastBreak = getStatus(opTimeToNextBreak)

    # Get the most recent fix
    lastFix = getStatus(breakTimeToFix)

    # Get the last inspection status
    lastInspection = getOne(rec for rec in statuses if rec['symptomCategory'] == 'INSPECTION')

    ret = { 'lastFix' : lastFix,
            'lastInspection' : lastInspection,
            'lastBreak': lastBreak,
            'lastOp' : lastOp,
            'lastStatus' : lastStatus
    }

    return ret

def doc2Str(doc, escIdToUnit, symptomCodeToSymptom):  
    if doc is None:
        return 'None'
    outputStr = '{esc}\t{code}\t{timeStr}'
    outputStr = outputStr.format(esc = escIdToUnit[doc['escalator_id']],
                                 code = symptomCodeToSymptom[doc['symptom_code']],
                                 timeStr = str(doc['time']))
    return outputStr


######################################################################
def groupStatusesByStationCode(statuses):
    _checkAllTimesNotNaive(statuses)
    stationCodeToStatus = defaultdict(list)
    for s in statuses:
        stationCodeToStatus[s['station_code']].append(s)
    return stationCodeToStatus

def groupStatusesByEscalator(statuses):
    _checkAllTimesNotNaive(statuses)
    escIdToStatus = defaultdict(list)
    for s in statuses:
        escIdToStatus[s['escalator_id']].append(s)
    return escIdToStatus

#####################################################################
# Determine the current escalator availabilities of the system
# Also compute the weighted availability and the station availability
# Exactly one of escalators or elevators must be True.
def getSystemAvailability(escalators=False, elevators=False, dbg=None):

    if dbg is None:
        dbg = dbGlobals.DBGlobals()
    db = dbg.getDB()

    if sum([escalators, elevators]) != 1:
        raise RuntimeError("escalators or elevators must be True, but not both.")

    latestStatuses = getLatestStatuses(escalators=escalators, elevators=elevators, dbg=dbg)
    N = len(latestStatuses)

    # Compute availability
    def computeAvailability(statusList):
        if not statusList:
            return 1.0
        N = len(statusList)
        numAvail = sum(1 for d in statusList if d['symptomCategory'] == 'ON')
        return float(numAvail)/N

    def computeWeightedAvailability(statusList):
        avail = [d for d in statusList if d['symptomCategory'] == 'ON']
        unavail = [d for d in statusList if d['symptomCategory'] != 'ON']
        availWeights = [stations.codeToStationData[d['station_code']]['escalatorWeight'] for d in avail]
        unavailWeights = [stations.codeToStationData[d['station_code']]['escalatorWeight'] for d in unavail]
        wA1 = sum(availWeights)
        wA2 = 1.0 - sum(unavailWeights)
        assert(abs(wA1 - wA2) < 1E-6)
        return wA1

    lastStatuses = [d['lastStatus'] for d in latestStatuses.itervalues()]
    lastStatuses = [s for s in lastStatuses if s is not None]
    numOp = sum(1 for d in lastStatuses if d['symptomCategory'] == 'ON')

    symptomCategoryToCount = Counter(d['symptomCategory'] for d in lastStatuses)
    symptomToCount = Counter(d['symptom'] for d in lastStatuses)

    # Compute overall availability
    availability = computeAvailability(lastStatuses)
    weightedAvailability = computeWeightedAvailability(lastStatuses) if escalators else 0.0

    # Compute availability for each station
    # Note: Some stations have multiple codes (Gallery Pl, L'Enfant, MetroCenter, FortTotten)
    # GP is 'F01' and 'B01' , L'Enfant is 'F03' and 'D03', FT is 'B06' and 'E06', MC is 'A01', 'C01'
    # stationCodeToAvailability: compute availability for each unique station code
    # stationToAvailability: compute availability for each station. Two codes which refer to
    #                        same station should return same value.
    stationCodeToStatuses = groupStatusesByStationCode(lastStatuses)
    stationGroups = stations.nameToCodes.values()
    stationToStatuses = {}
    for codeGroup in stationGroups:
        allStatuses = [s for c in codeGroup for s in stationCodeToStatuses[c]]
        stationToStatuses.update((c, allStatuses) for c in codeGroup)

    stationCodeToAvailability = dict((k, computeAvailability(v)) for k,v in stationCodeToStatuses.iteritems())
    stationToAvailability = dict((k, computeAvailability(v)) for k,v in stationToStatuses.iteritems())

    ret = { 'availability' : availability,
            'weightedAvailability' : weightedAvailability,
            'numOp' : numOp,
            'numEsc' : N,
            'symptomCategoryToCount' : symptomCategoryToCount,
            'symptomToCount' : symptomToCount,
            'stationCodeToAvailability' : stationCodeToAvailability,
            'stationToAvailability' : stationToAvailability,
            'stationCodeToStatuses' : stationCodeToStatuses,
            'stationToStatuses' : stationToStatuses,
            'escToLatest' : latestStatuses,
            'lastStatuses' : lastStatuses
          }

    return ret

#########################################################
# ONLY WORKS WITH ESCALATORS, NOT ELEVATORS
# Get escalator data summary for a single station
# for a given time period.
# This returns a dictionary with the sames keys as summarizeStatuses,
# with additional keys:
# - escUnitIds
# - escToSummary
# - escToStatuses
def getStationSummary(stationCode, startTime = None, endTime = None, dbg=None):

    if dbg is None:
        dbg = dbGlobals.DBGlobals()

    # Convert startTime and endTime to utcTimeZone, if necessary
    if startTime is not None:
        startTime = toUtc(startTime)
    if endTime is not None:
        endTime = toUtc(endTime)

    stationData = stations.codeToStationData[stationCode]
    allCodes = set(stationData['allCodes'])
    escList = [d for d in dbg.escIdToEscData.itervalues() if d['station_code'] in allCodes and d['unit_type']=='ESCALATOR']
    escUnitIds = [d['unit_id'] for d in escList]
    assert(len(escList) == stationData['numEscalators'])
    curTime = utcnow()

    # First, compute a summary on each escalator in the station
    escToSummary = {}
    escToStatuses = {}

    for escUnitId in escUnitIds:
        statuses = getEscalatorStatuses(escUnitId=escUnitId, startTime = startTime, endTime=endTime, dbg=dbg)
        escToStatuses[escUnitId] = statuses
        if not statuses:
            continue

        # Compute a summary on these statuses.
        # Remember statuses are sorted in descending order
        st = startTime if startTime is not None else statuses[-1]['time']
        et = endTime if endTime is not None else curTime

        escSummary = summarizeStatuses(statuses, st, et)
        escSummary['statuses'] = statuses
        escToSummary[escUnitId] = escSummary

    # Next, compute a summary the group of escalators as whole
    stationSummary = mergeEscalatorSummaries(escToSummary.values())
    stationSummary['escUnitIds'] = escUnitIds
    stationSummary['escToSummary'] = escToSummary
    stationSummary['escToStatuses'] = escToStatuses
    return stationSummary

##################################
# Get a snapshot of the station right now
def getStationSnapshot(stationCode, dbg=None):

    if dbg is None:
        dbg = dbGlobals.DBGlobals()
    db = dbg.getDB()

    stationData = stations.codeToStationData[stationCode]
    allCodes = set(stationData['allCodes'])

    # Get escalator data for escalators in this station
    escIds = dbg.getEscalatorIds()
    escDataList = (dbg.escIdToEscData[escId] for escId in escIds)
    escDataList = [d for d in escDataList if d['station_code'] in allCodes]
    escUnitIds = [d['unit_id'] for d in escDataList]
    assert(len(escDataList) == stationData['numEscalators'])

    curTime = utcnow()

    def getLatestStatus(escUnitId):
        escId = dbg.unitToEscId[escUnitId]
        status = db.escalator_statuses.find_one({'escalator_id' : escId}, sort=[('time', pymongo.DESCENDING)])
        status['time'] = status['time'].replace(tzinfo=tzutc)
        addStatusAttr([status], dbg=dbg)
        return status
        
    escToLatest = dict((escUnitId, getLatestStatus(escUnitId)) for escUnitId in escUnitIds)
    numWorking = sum(1 for s in escToLatest.itervalues() if s['symptomCategory']=='ON')
    numEscalators = len(escDataList)
    availability = float(numWorking)/numEscalators if numEscalators > 0 else 0.0

    ret = {'escalatorList' : escDataList,
           'escUnitIds' : escUnitIds,
           'escUnitIdToLatestStatus' : escToLatest,
           'numEscalators' : numEscalators,
           'numWorking' : numWorking,
           'availability' : availability}

    # Tack on the stationData to the return value
    ret.update(stationData)
    return ret

########################################
# Merge a list of escalator summaries produced by summarizeStatuses
# into a single summary. This is useful for compiling
# a summary for a single station
def mergeEscalatorSummaries(escalatorSummaryList):

    # Accumulate a list of symptom to time dictionaries
    def accumD(timeDictList):
        merged = defaultdict(lambda: 0.0)
        for td in timeDictList:
            for k,v in td.iteritems():
                merged[k] += v
        return merged

    # Accumulate a list of numbers
    def accum(values):
        return sum(values)

    keyAccumulators = [ ('numBreaks', accum),
                        ('numFixes', accum),
                        ('numInspections', accum),
                        ('symptomCodeToTime', accumD),
                        ('symptomCodeToAbsTime', accumD),
                        ('symptomCategoryToTime', accumD),
                        ('symptomCategoryToAbsTime', accumD),
                        ('availableTime', accum),
                        ('metroOpenTime', accum),
                        ('absTime', accum) ]
    merged = {}
    for k, af in keyAccumulators:
        val = af(d[k] for d in escalatorSummaryList)
        merged[k] = val
    # Compute the availability on this merged set
    openTime = float(merged['metroOpenTime'])
    availTime = float(merged['availableTime'])
    merged['availability'] = availTime/openTime if openTime > 0.0 else 1.0
    return merged


#################################################
# Get statuses for a single escalator
#
# startTime and endTime can be used to return statuses for a given time period.
# If startTime or endTime are provided, the status list is padded
# with statuses that preceed and follow the statuses in the time range in
# order to provide context.
def getEscalatorStatuses(escId=None, escUnitId=None, startTime = None, endTime = None, dbg=None):

    if dbg is None:
        dbg = dbGlobals.DBGlobals()
    db = dbg.getDB()

    # Convert startTime and endTime to utcTimeZone, if necessary
    if startTime is not None:
        startTime = toUtc(startTime)
    if endTime is not None:
        endTime = toUtc(endTime)

    if escId is None:
        if escUnitId is None:
            raise RuntimeError('getEscalatorDetails: escId or escUnitId must be provided.')
        escId =  dbg.unitToEscId[escUnitId]

    # Find latest statuses for this escalator
    sort_params = [('time', pymongo.DESCENDING)]
    query = {'escalator_id' : escId}
    timeQuery = {}
    if startTime is not None:
        timeQuery['$gte'] = startTime
    if endTime is not None:
        timeQuery['$lte'] = endTime
    if timeQuery:
        query['time'] = timeQuery
    cursor = db.escalator_statuses.find(query, sort=sort_params)
    statuses = list(cursor)

    # If startTime is specified, give all statuses from first operational
    # status which preceeds startTime
    if startTime is not None and ((not statuses) or (statuses[-1]['symptom_code'] != OP_CODE)):
        firstStatusTime = startTime
        query = {'escalator_id' : escId,
                 'time' : {'$lt' : firstStatusTime}}
        sort_params = [('time', pymongo.DESCENDING)]
        c = db.escalator_statuses.find(query, sort=sort_params)
        preceeding = []
        for s in c:
            preceeding.append(s)
            if s['symptom_code'] == OP_CODE:
                break
        statuses.extend(preceeding)

    # If endTime is specified, give all statuses after the first
    # operational status which follows endTime
    if endTime is not None and ((not statuses) or (statuses[0]['symptom_code'] != OP_CODE)):
        lastStatusTime = endTime
        query = {'escalator_id' : escId,
                 'time' : {'$gt' : lastStatusTime}}
        sort_params = [('time', pymongo.ASCENDING)]
        c = db.escalator_statuses.find(query, sort=sort_params)
        following = []
        for s in c:
            following.append(s)
            if s['symptom_code'] == OP_CODE:
                break
        # Following are in ascending order. Reverse the order to make it descending.
        following = following[::-1]
        statuses = following + statuses

    # Add tzinfo to all status
    for status in statuses:
        status['time'] = status['time'].replace(tzinfo=tzutc)
    addStatusAttr(statuses, dbg=dbg)
    return statuses

########################################################
# Given a status list for a single escalator, sorted in descending
# time order, compute a summary:
# - numBreaks
# - numInspections
# - time spent in each status code
# - metro open time spent in each status code
# startTime and endTime must be provided to properly compute the times.
def summarizeStatuses(statusList, startTime, endTime):

    _checkAllTimesNotNaive(statusList)

    # Convert startTime and endTime to utcTimeZone, if necessary
    if startTime is not None:
        startTime = toUtc(startTime)
    if endTime is not None:
        endTime = toUtc(endTime)

    if not statusList:
        return {}

    if(startTime > endTime):
       raise RuntimeError('summarizeStatuses: bad startTime/endTime')

    # Reverse the sort order so statuses are in asending order
    fullStatusList = statusList[::-1]
    statusGroup = StatusGroup(fullStatusList, startTime=startTime, endTime=endTime)
    statusList = statusGroup.statuses

    if not statusList:
        default_ret = { 'numBreaks' : 0,
                        'numFixes' : 0,
                        'numInspections' : 0,
                        'symptomCodeToTime' : {},
                        'symptomCodeToAbsTime' : {},
                        'symptomCategoryToTime' : {},
                        'symptomCategoryToAbsTime' : {},
                        'availableTime' : 0,
                        'availability' : 1.0,
                        'metroOpenTime' : 0.0,
                        'brokenTimePercentage' : 0.0,
                        'absTime' : 0.0}
        return default_ret

    breakStatuses = statusGroup.breakStatuses
    fixStatuses = statusGroup.fixStatuses
    inspectionStatuses = statusGroup.inspectionStatuses
    
    numBreaks = len(breakStatuses)
    numFixes = len(fixStatuses)
    numInspections = len(inspectionStatuses)

    for s in statusList:
        if any(s.get(k, None) is None for k in ('time', 'end_time')):
            raise RuntimeError('summarizeStatuses: status is missing end_time field')

    # Summarize the time allocation to various symptoms for this time window
    symptomCodeToTime = statusGroup.symptomCodeTimeAllocation
    symptomCodeToAbsTime = statusGroup.symptomCodeAbsTimeAllocation
    symptomCategoryToTime = statusGroup.timeAllocation
    symptomCategoryToAbsTime = statusGroup.absTimeAllocation

    availTime = symptomCategoryToTime['ON']
    timeRange = statusGroup.timeRange
    metroOpenTime = timeRange.metroOpenTime
    absTime = timeRange.absTime
    availability = availTime/metroOpenTime if metroOpenTime > 0.0 else 1.0

    ret = { 'numBreaks' : numBreaks,
            'numFixes' : numFixes,
            'numInspections' : numInspections,
            'symptomCodeToTime' : symptomCodeToTime,
            'symptomCodeToAbsTime' : symptomCodeToAbsTime,
            'symptomCategoryToTime' : symptomCategoryToTime,
            'symptomCategoryToAbsTime' : symptomCategoryToAbsTime,
            'availableTime' : availTime,
            'availability' : availability,
            'brokenTimePercentage' : statusGroup.brokenTimePercentage,
            'metroOpenTime' : metroOpenTime,
            'absTime' : absTime}

    return ret


############################################################################
# Get a summary of all escalators for the specified time period
def getAllEscalatorSummaries(startTime=None, endTime=None, escalators=False, elevators=False, dbg=None):

    if dbg is None:
        dbg = dbGlobals.DBGlobals()
    db = dbg.getDB()

    # Convert startTime and endTime to utcTimeZone, if necessary
    if startTime is not None:
        startTime = toUtc(startTime)
    if endTime is not None:
        endTime = toUtc(endTime)

    if escalators and not elevators:
        escIds = dbg.getEscalatorIds()
    elif elevators and not escalators:
        escIds = dbg.getElevatorIds()
    else:
        # Get both escalators and elevators
        escIds = db.escalators.find({}, fields=['_id'])

    curTime = utcnow()

    escToSummary = {}

    # NOTE: This function could be improved by making a single call to db.escalator_statuses.find() and
    # aggregating.
    for escId in escIds:
        gevent.sleep(0.0)
        statuses = getEscalatorStatuses(escId=escId, startTime = startTime, endTime = endTime, dbg=dbg)
        et = endTime if endTime is not None else curTime
        st = startTime if startTime is not None else min(s['time'] for s in statuses)
        summary = summarizeStatuses(statuses, st, et)
        summary['statuses'] = statuses
    
        # Add escalator meta-data to the summary
        escData = dbg.escIdToEscData[escId]
        summary.update(escData)

        escToSummary[escId] = summary

    return escToSummary

###############################################################################
# Get all escalator statuses.
# Return a dictionary from escalator to status list, in chronological order
def getAllEscalatorStatuses(dbg=None):
    if dbg is None:
        dbg = dbGlobals.DBGlobals()
    db = dbg.getDB()
    
    statuses = list(db.escalator_statuses.find({}, sort=[('time',pymongo.ASCENDING)]))
    escIdToStatuses = defaultdict(list)
    for s in statuses:
        escIdToStatuses[s['escalator_id']].append(s)
    for sl in escIdToStatuses.itervalues():
        for s in sl:
            s['time'] = s['time'].replace(tzinfo=tzutc)
        addStatusAttr(sl[::-1], dbg=dbg)
    return escIdToStatuses
