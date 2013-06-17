# Utilities for interacting with a MongoDB
# Functionality for updating the databases
import pymongo
import sys
import os
from collections import defaultdict, Counter
from datetime import datetime, time, date, timedelta
from operator import itemgetter
import copy

from escalatorUtils import symptomToCategory, OPERATIONAL_CODE
import stations
from metroTimes import TimeRange

invDict = lambda d: dict((v,k) for k,v in d.iteritems())

###############################
# GLOBALS
db = None
unitToEscId = None
escIdToUnit = None
symptomToId = None
symptomCodeToSymptom = None
escIdToEscData = None
opCode = OPERATIONAL_CODE
################################



################################
def updateGlobals(force=True):
    global db, unitToEscId, escIdToUnit, symptomToId, symptomCodeToSymptom, escIdToEscData
    globalList = [db, unitToEscId, escIdToUnit, symptomToId, symptomCodeToSymptom, escIdToEscData]
    if force or any(g is None for g in globalList):
        db = getDB()

        # Add the operational code
        db.symptom_codes.find_and_modify({'_id' : OPERATIONAL_CODE},
                                         update = {'_id' : OPERATIONAL_CODE,
                                                   'symptom_desc' : 'OPERATIONAL'},
                                         upsert=True)

        unitToEscId = getUnitToId(db)
        escIdToUnit = invDict(unitToEscId)
        symptomToId = getSymptomToId(db)
        opCode = symptomToId['OPERATIONAL']
        symptomCodeToSymptom = invDict(symptomToId)
        escList = list(db.escalators.find())
        escIdToEscData = dict((d['_id'], d) for d in escList)

###############################
def getDB():
    global db  

    if db is not None:
        return db

    host = os.environ["OPENSHIFT_MONGODB_DB_HOST"]
    port = int(os.environ["OPENSHIFT_MONGODB_DB_PORT"])
    user = os.environ["OPENSHIFT_MONGODB_DB_USERNAME"]
    password = os.environ["OPENSHIFT_MONGODB_DB_PASSWORD"]
    client = pymongo.MongoClient(host, port)

    # Try authenticating with admin
    db = client.admin
    #serr('Attempting Authentication\n')
    res = db.authenticate(user, password)
    #serr('Authenticate returned: %s\n'%str(res))

    db = client.MetroEscalators
    updateGlobals()
    return db

########################################
# Create dictionary from escalator unit id
# to the pymongo id
def getUnitToId(db):
    escList = list(db.escalators.find())
    unitToEscId = dict((d['unit_id'],d['_id']) for d in escList)
    return unitToEscId

##########################################
# Create dictionary from symptom to symptom id
def getSymptomToId(db):
    symptoms = list(db.symptom_codes.find())
    symptomDict = dict((d['symptom_desc'],d['_id']) for d in symptoms)
    return symptomDict

def getEsc(db, escId):
    c = db.escalators.find({'_id' : escId})
    return getOne(c)

##########################################
# Get one item from the cursor. Return None if there is no item.
def getOne(cursor):
    try:
        res = next(cursor)
        return res
    except StopIteration:
        return None

def getSome(cursor, N):
    results = []
    for res in cursor:
        results.append(res)
        if len(res) == N:
            break
    return results

def updateAppState(db, lastRunTime = None, nextDailyStatusTime = None):
    update = {}
    if lastRunTime is not None:
        update['lastRunTime'] = lastRunTime
    if nextDailyStatsTime is not None:
        update['nextDailyStatsTime'] = nextDailyStatusTime
    if not update:
        return
    update = {'$set' : update}
    db.app_state.find_and_modify({'_id' : 1}, update=update, upsert=True)

########################################
# Initialize the escalator databased with entries
# Initialize the escalator_statuses database with default
# OPERATIONAL entries
def initializeEscalators(db, escDataList, curTime):
    for d in escDataList:
        addEscalator(db, curTime, d['unit_id'], d['station_code'],
                         d['station_name'], d['esc_desc'],
                         d.get('station_desc',None))
    updateGlobals()

########################################
# Add escalator to the database if it does not exist already.
# Note: This will not modify the escalator attributes if a document
# with a matching unit_id already exists
def addEscalator(db, curTime, unit_id, station_code, station_name, esc_desc, station_desc=None):

    # See if this escalator already exists in the database
    db.escalators.ensure_index('unit_id')
    query = {'unit_id' : unit_id}
    count = db.escalators.find(query).count()
    assert(count in (0,1))

    # Update/Add the entry.
    #db.escalators.find_and_modify(query=query, update=d, upsert=True)

    # Add the entry if necessary
    if count == 0:
        d = { 'unit_id' : unit_id,
              'station_code' : station_code,
              'station_name' : station_name,
              'esc_desc' : esc_desc,
              'station_desc' : station_desc if station_desc is not None else ''
            }
        escId = db.escalators.insert(d)

        # Add a new entry to the escalator_statuses collection
        statusCount = db.escalator_statuses.find({'escalator_id' : escId}).count()
        assert(statusCount == 0)
        symptomToId = getSymptomToId(db)
        opCode = symptomToId['OPERATIONAL']
        doc = {'escalator_id' : escId,
               'time' : curTime - timedelta(milliseconds=1),
               'tickDelta' : 0,
               'symptom_code' : opCode}
        db.escalator_statuses.insert(doc)

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
    station_desc = ''
    station_name = inc.StationName
    if ',' in station_name:
        station_name, station_desc = station_name.split(',', 1)
    station_name = station_name.strip()
    station_desc = station_desc.strip()
    addEscalator(db, curTime, inc.UnitId, inc.StationCode, station_name,
       esc_desc = inc.LocationDescription, station_desc = station_desc)

    # Add the symptom code to the database
    addSymptomCode(db, inc.SymptomCode, inc.SymptomDescription)

    updateGlobals()

##########################################################
# Retrieve information about the latest statuses for all escalators
# Return a dictionary (key=escalator_id, value=status_dict)
# status_dict is dictionary returned by getKeyStatuses
def getLatestStatuses(db):

    updateGlobals(force=False)

    # Get the unique escalator ids
    esc_ids = db.escalator_statuses.distinct('escalator_id')

    db.escalator_statuses.ensure_index([('escalator_id', pymongo.ASCENDING),
                                        ('time', pymongo.DESCENDING)])
    getTime = lambda d: d.get('time', None) if d is not None else None
        
    escToStatuses = {}

    for esc_id in esc_ids:

        # Find latest 1000 statuses for this escalator
        sort_params = [('time', pymongo.DESCENDING)]
        cursor = db.escalator_statuses.find({'escalator_id' : esc_id}, sort=sort_params)
        latest = getSome(cursor, 1000) # Latest status updates for this escalator


        keyStatuses = getKeyStatuses(latest)
        escToStatuses[esc_id] = keyStatuses

    return escToStatuses

###############################################
# Add attributes to each escalator_status doc
# in a sorted list of escalator docs for a single escalator.
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
def addStatusAttr(statusList):

    updateGlobals(force=False)

    if not statusList:
        return

    # Check that these statuses concern a single escalator
    escids = set(s['escalator_id'] for s in statusList)
    if not len(escids)==1:
        raise RuntimeError('makeFullStatuses: received status list for multiple escalators!')
    escId = escids.pop()

    # Get the escalator data for this escalator
    escData = escIdToEscData.get(escId, None)
    if escData is None:
        raise RuntimeError('makeFullStatuses: Missing escalator data for escalator id: %s'%str(escId))

    lastTime = None
    lastIndex = len(statusList)-1
    for i, d in enumerate(statusList):
        # Add end_time
        if i != lastIndex:
            statusList[i+1]['end_time'] = d['time']
        if i > 0 and d['time'] > lastTime:
            raise RuntimeError('makeFullStatuses: escalator statuses not properly sorted!')
        # Add symptom fields
        symp = symptomCodeToSymptom[d['symptom_code']]
        d['symptom'] = symp
        d['symptomCategory'] = symptomToCategory[symp]
        # Add escalator data fields 
        escDataKeys = ['unit_id', 'station_name', 'station_desc', 'station_code', 'esc_desc']
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
# first broken status of the stretch of brokeness.
def getKeyStatuses(statuses):

    updateGlobals(force=False)

    # Check that these statuses concern a single escalator
    escids = set(s['escalator_id'] for s in statuses)
    if not len(escids)==1:
        raise RuntimeError('getKeyStatuses: received status list for multiple escalators!')

    # Sort statuses by time in descending order
    statusesRevCron = sorted(statuses, key = itemgetter('time'), reverse=True)
    statusesCron = statusesRevCron[::-1]
    statuses = statusesRevCron

    # Add additional attributes to all statuses
    addStatusAttr(statuses)

    # Organize the operational statuses and breaks.
    # Associate each operational status with the next break which follows it
    # Associate each break with the next operational status which follows it
    ops = [rec for rec in statuses if rec['symptomCategory'] == 'ON']
    opTimes = [rec['time'] for rec in ops]
    breaks = [rec for rec in statuses if rec['symptomCategory'] == 'BROKEN']
    breakTimes = [rec['time'] for rec in breaks]

    def getFirstStatusSince(statusList, time):
        statusList = sorted(statusList, key = itemgetter('time')) # in time ascending
        myRecs = (rec for rec in statusList if rec['time'] > time)
        return getOne(myRecs)

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

def doc2Str(doc):  
    if doc is None:
        return 'None'
    outputStr = '{esc}\t{code}\t{timeStr}'
    outputStr = outputStr.format(esc = escIdToUnit[doc['escalator_id']],
                                 code = symptomCodeToSymptom[doc['symptom_code']],
                                 timeStr = str(doc['time']))
    return outputStr

########################################################
# Determine which escalators that have changed status,
# and update the database with units have been updated.
# Return a dictionary of escalator id to status dictionary for escalators
# which have changed statuses.
# The status dictionary has keys:
# - lastFix
# - lastBreak
# - lastInspection
# - lastOp
# - lastStatus: The status before this tick's update
# - newStatus: The updated status
def processIncidents(db, curIncidents, curTime, tickDelta, log=sys.stdout):

    updateGlobals(force=False)

    log = log.write
    log('dbUtils.processIncidents: Processing %i incidents\n'%len(curIncidents))
    log('escalator_statuses has %i documents\n'%(db.escalator_statuses.find().count()))
    sys.stdout.flush()

    # Add any escalators or symptom codes if we are seeing them for the first time
    for inc in curIncidents:
        updateDBFromIncidentData(db, inc, curTime)

    # Create dictionary of escalator to the current status
    escIdToCurStatus = defaultdict(lambda: opCode)
    incStatus = lambda inc: (unitToEscId[inc.UnitId], symptomToId[inc.SymptomDescription])
    escIdToCurStatus.update(incStatus(inc) for inc in curIncidents)

    # Get the last known statuses for all escalators.
    # Recast escStatuses as a defaultdict
    escStatusItems = getLatestStatuses(db).items()
    default_entry = {'lastFix' : None,
                     'lastBreak' : None,
                     'lastInspection' : None,
                     'lastOp' : None,
                     'lastStatus' : None}
    escStatuses = defaultdict(lambda: default_entry)
    escStatuses.update(escStatusItems)
    escIdToLastStatus = defaultdict(lambda: opCode)
    escIdToLastStatus.update((escId, escStatus['lastStatus']['symptom_code']) for
                              escId, escStatus in escStatuses.iteritems())

    #### DEBUG #########################
#    docToStr = lambda d: doc2Str(d)
#    sys.stderr.write('-'*50 + '\n\n')
#    for escId,escData in escStatusItems:
#        lines = ['Statuses for escalator %s'%(escIdToUnit[escId])]
#        lines.extend('%s %s'%(k, docToStr(v)) for k,v in escData.iteritems())
#        lines.append('-----------------')
#        sys.stderr.write('%s\n'%('\n'.join(lines)))
#    sys.stderr.write('-'*50 + '\n\n')
    ####################################

    # Determine those escalators that have changed status
    escIds = sorted(set(escIdToCurStatus.keys() + escIdToLastStatus.keys()))
    oldStatuses = (escIdToLastStatus[escId] for escId in escIds)
    newStatuses = (escIdToCurStatus[escId] for escId in escIds)
    changedStatus = [(escId, oldStatus, newStatus)
                     for escId,oldStatus,newStatus in zip(escIds, oldStatuses, newStatuses)
                     if oldStatus != newStatus]

    # Update the database with escalators that have changed status 
    docs = []
    changedStatusDict = {}
    for escId, oldStatus, newStatus in changedStatus:
        doc = {'escalator_id' : escId,
               'time' : curTime,
               'tickDelta' : tickDelta,
               'symptom_code' : int(newStatus)}
        docs.append(doc)
        changedStatusData = escStatuses[escId]
        changedStatusData['newStatus'] = doc
        changedStatusDict[escId] = changedStatusData

        #### DEBUG
#        sys.stderr.write('Esc Name: %s OldStatus: %s NewStatus: %s\n' % \
#                         (escIdToUnit[escId], symptomCodeToSymptom.get(oldStatus, 'None'),
#                                              symptomCodeToSymptom.get(newStatus, 'None'))
#                         )
        ####
    if docs:
        db.escalator_statuses.insert(docs)
#        #### DEBUG
#        sys.stderr.write('-'*50 + '\n\n')
#        sys.stderr.write('Inserting %i statuses into escalator_statuses collection\n'%len(docs))
#        docToStr = lambda d: doc2Str(d)
#        for doc in docs:
#            sys.stderr.write('%s\n'%docToStr(doc))
#        sys.stderr.write('-'*50 + '\n\n')
#        ####
    return changedStatusDict

def groupStatusesByStationCode(statuses):
    stationCodeToStatus = defaultdict(list)
    for s in statuses:
        stationCodeToStatus[s['station_code']].append(s)
    return stationCodeToStatus

#####################################################################
# Determine the escalator availabilities of the system
# Also compute the weighted availability and the station availability
def getSystemAvailability():
    db = getDB()
    latestStatuses = getLatestStatuses(db)
    N = len(latestStatuses)

    # Compute availability
    def computeAvailability(statusList):
        if not statusList:
            return 0.0
        N = len(statusList)
        numAvail = sum(1 for d in statusList if d['symptomCategory'] == 'ON')
        return float(numAvail)/N

    def computeWeightedAvailability(statusList):
        avail = [d for d in statusList if d['symptomCategory'] == 'ON']
        unavail = [d for d in statusList if d['symptomCategory'] != 'ON']
        availWeights = [stations.codeToData[d['station_code']]['escalatorWeight'] for d in avail]
        unavailWeights = [stations.codeToData[d['station_code']]['escalatorWeight'] for d in unavail]
        wA1 = sum(availWeights)
        wA2 = 1.0 - sum(unavailWeights)
        assert(abs(wA1 - wA2) < 1E-6)
        return wA1

    lastStatuses = [d['lastStatus'] for d in latestStatuses.itervalues()]
    numOp = sum(1 for d in lastStatuses if d['symptomCategory'] == 'ON')

    symptomCategoryToCount = Counter(d['symptomCategory'] for d in lastStatuses)
    symptomToCount = Counter(d['symptom'] for d in lastStatuses)

    # Compute overall availability
    availability = computeAvailability(lastStatuses)
    weightedAvailability = computeWeightedAvailability(lastStatuses)

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


#################################################
# Get statuses for a single escalator
#
# startTime and endTime can be used to return statuses for a given time period.
# If startTime or endTime are provided, the status list is padded
# with statuses that preceed and follow the statuses in the time range in
# order to provide context.
def getEscalatorStatuses(escId=None, escUnitId=None, startTime = None, endTime = None):

    if escId is None:
        if escUnitId is None:
            raise RuntimeError('getEscalatorDetails: escId or escUnitId must be provided.')
        escId =  unitToEscId[escUnitId]

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
    addStatusAttr(statuses)

    # If startTime is specified, give all statuses from first operational
    # status which preceeds startTime
    if startTime is not None and (not statuses) or (statuses[-1]['symptom_code'] != opCode):
        firstStatusTime = startTime
        query = {'escalator_id' : escId,
                 'time' : {'$lt' : firstStatusTime}}
        sort_params = [('time', pymongo.DESCENDING)]
        c = db.escalator_statuses.find(query, sort=sort_params)
        preceeding = []
        for s in c:
            preceeding.append(s)
            if s['symptom_code'] == opCode:
                break
        statuses.extend(preceeding)

    # If endTime is specified, give all statuses after the first
    # operational status which follows endTime
    if endTime is not None and (not statuses) or (statuses[0]['symptom_code'] != opCode):
        lastStatusTime = endTime
        query = {'escalator_id' : escId,
                 'time' : {'$gt' : lastStatusTime}}
        sort_params = [('time', pymongo.ASCENDING)]
        c = db.escalator_statuses.find(query, sort=sort_params)
        following = []
        for s in c:
            following.append(s)
            if s['symptom_code'] == opCode:
                break
        # Following are in ascending order. Reverse the order to make it descending.
        following = following[::-1]
        statuses = following + statuses
    
    addStatusAttr(statuses)
    return statuses

########################################################
# Given a status list for a single escalator, sorted in descending
# time order, compute a summary:
# - numBreaks
# - numInspections
# - time spent in each status code
# - metro open time spent in each status code
def summarizeStatuses(statusList, startTime, endTime):

    if not statusList:
        import pdb; pdb.set_trace()
        return {}

    if (startTime is not None) and (endTime is not None) \
       and (startTime > endTime):
       raise RuntimeError('summarizeStatuses: bad startTime/endTime')

    statusList = copy.deepcopy(statusList)

    addStatusAttr(statusList)

    # Reverse the sort order so statuses are in asending order
    fullStatusList = statusList[::-1]
    statusList = copy.deepcopy(fullStatusList) # This will be trimmed to startTime/endTime

    def filterStatusList(sl):
        if startTime is not None:
            sl = [s for s in sl if s['time'] >= startTime]
        if endTime is not None:
            sl = [s for s in sl if s['time'] < endTime]
        return sl

    # We need the full context of the statuses in this time period
    # in order to properly count the number of breaks, fixes, and inspections
    # allocated to this time period.
    fullStatusGroup = StatusGroup(fullStatusList)
    breakStatuses = filterStatusList(fullStatusGroup.breakStatuses())
    fixStatuses = filterStatusList(fullStatusGroup.fixStatuses())
    inspectionStatuses = filterStatusList(fullStatusGroup.inspectionStatuses())
    numBreaks = len(breakStatuses)
    numFixes = len(fixStatuses)
    numInspections = len(inspectionStatuses)

    # The statusList may have statuses that provide context before and after the  startTime/endTime
    # If necessary, adjust the statusList to restrict statuses to the specified startTime/endTime.
    if startTime is not None:
        beforeStart = [(i,s) for i,s in enumerate(statusList) if s['time'] < startTime]
        firstInd, firstStatus = beforeStart[-1] if beforeStart else (None, None)
        # Adjust the beginning of the list, if necessary
        if firstInd is not None:
            statusList = statusList[firstInd:]
            assert(statusList[0] is firstStatus)

    if endTime is not None:
        afterEnd = [(i,s) for i,s in enumerate(statusList) if s['time'] >= endTime]
        afterEndInd, afterEndStatus = afterEnd[0] if afterEnd else (None, None)
        # Adjust the beginning of the list, if necessary
        if afterEndInd is not None:
            statusList = statusList[:afterEndInd]

    if not statusList:
        import pdb; pdb.set_trace()
        return {}

    if startTime:
        statusList[0]['time'] = startTime

    lastStatus = statusList[-1]
    if endTime:
        lastStatus['end_time'] = endTime
    elif 'end_time' not in lastStatus:
        lastStatus['end_time'] = lastStatus['time']
            
    for s in statusList:
        if any(s.get(k, None) is None for k in ('time', 'end_time')):
            raise RuntimeError('summarizeStatuses: status is missing end_time field')

    # Summarize the time allocation to various symptoms for this time window
    sg = StatusGroup(statusList)
    symptomCodeToTime = sg.symptomCodeToTime
    symptomCodeToAbsTime = sg.symptomCodeToAbsTime
    symptomCategoryToTime = sg.symptomCategoryToTime
    symptomCategoryToAbsTime = sg.symptomCategoryToAbsTime

    availTime = symptomCategoryToTime['ON']
    totalTime = TimeRange(startTime, endTime).metroOpenTime()
    availability = availTime/totalTime if totalTime > 0.0 else 1.0


    ret = { 'numBreaks' : numBreaks,
            'numFixes' : numFixes,
            'numInspections' : numInspections,
            'symptomCodeToTime' : symptomCodeToTime,
            'symptomCodeToAbsTime' : symptomCodeToAbsTime,
            'symptomCategoryToTime' : symptomCategoryToTime,
            'symptomCategoryToAbsTime' : symptomCategoryToAbsTime,
            'availableTime' : availTime,
            'availability' : availability,
            'metroOpenTime' : totalTime}

    return ret


    
class StatusGroup(object):
    """
    Helper class to summarize a time series of statuses for a single escalator.
    """
    def __init__(self, statuses):

        self.statuses = statuses

        if not self.statuses:
            return

        # The statuses must be sorted in ascending order
        lastTime = None
        for s in self.statuses:
            if lastTime and s['time'] < lastTime:
                raise RuntimeError('StatusGroup: statuse are not sorted in ascending order')
            lastTime = s['time']

        self.startTime = statuses[0]['time']
        self.endTime = statuses[-1].get('end_time', None)
        if self.endTime is None:
            self.endTime = statuses[-1]['time']

        self.timeRange = TimeRange(self.startTime, self.endTime)
        self.absTime = self.timeRange.absTime
        self.metroOpenTime = self.timeRange.metroOpenTime

        self.symptomCategoryCounts = Counter(s['symptomCategory'] for s in self.statuses)

        self.symptomCodeToTimeRanges = None
        self.symptomCategoryToTimeRanges = None
        self.symptomCategoryToTime = None
        self.symptomCategoryToAbsTime = None
        self.symptomCodeToTime = None
        self.symptomCodeToAbsTime = None
        self.setTimes()


    ############################
    # Count the number of transitions to a broken state within
    # this group of statuses. If the first status is broken, it does
    # not count as a break.
    # Only count at most one break between operational states
    def breakStatuses(self):
        wasBroken = False
        #breakCount = 0
        breakStatuses = []
        for s in self.statuses:
            if s['symptomCategory'] == 'ON':
                wasBroken = False
            elif s['symptomCategory'] == 'BROKEN':
                if not wasBroken:
                    #breakCount += 1
                    breakStatuses.append(s)
                wasBroken = True
        return breakStatuses

    ############################
    # Count the number of resolved broken states.
    # Transitions such as : CALLBACK/REPAIR -> MINOR REPAIR -> OPERATIONAL only
    # should count as a single fix.
    # this group of statuses
    def fixStatuses(self):
        wasBroken = False
        fixStatuses = []
        for s in self.statuses:
            if s['symptomCategory'] == 'BROKEN':
                wasBroken = True
            elif s['symptomCategory'] == 'ON':
                if wasBroken:
                    fixStatuses.append(s)
                wasBroken = False
        return fixStatuses

    ############################
    # Count the number of inspection statuses
    # Only get the first inspection state between operational states
    def inspectionStatuses(self):
        wasInspection = False
        iStatuses = []
        for s in self.statuses:
            if s['symptomCategory'] == 'INSPECTION':
                if not wasInspection:
                    iStatuses.append(s)
                wasInspection = True
            elif s['symptomCategory'] == 'ON':
                wasInspection = False
        return iStatuses

    ######################################
    # Get the amount of metro open time allocated to each symptom category
    def getTimeAllocation(self):
        symptomCategoryToTime = defaultdict(lambda: 0.0)
        for symptomCategory, trList in self.symptomCategoryToTimeRanges.iteritems():
            symptomCategoryToTime[symptomCategory] = sum(tr.metroOpenTime() for tr in trList)
        totalTime = sum(symptomCategoryToTime.values())
        assert(abs(totalTime - self.timeRange.metroOpenTime()) < 1E-3)
        return symptomCategoryToTime

    ######################################
    # Get the amount of absolute time allocated to each symptom category
    def getAbsTimeAllocation(self):
        symptomCategoryToTime = defaultdict(lambda: 0.0)
        for symptomCategory, trList in self.symptomCategoryToTimeRanges.iteritems():
            symptomCategoryToTime[symptomCategory] = sum(tr.absTime() for tr in trList)
        totalTime = sum(symptomCategoryToTime.values())
        assert(abs(totalTime - self.timeRange.absTime()) < 1E-3)
        return symptomCategoryToTime

    ######################################
    # Get the amount of metro open time allocated to each symptom category
    def getSymptomTimeAllocation(self):
        symptomCodeToTime = defaultdict(lambda: 0.0)
        for symptomCode, trList in self.symptomCodeToTimeRanges.iteritems():
            symptomCodeToTime[symptomCode] = sum(tr.metroOpenTime() for tr in trList)
        totalTime = sum(symptomCodeToTime.values())
        assert(abs(totalTime - self.timeRange.metroOpenTime()) < 1E-3)
        return symptomCodeToTime

    ######################################
    # Get the amount of absolute time allocated to each symptom category
    def getSymptomAbsTimeAllocation(self):
        symptomCodeToTime = defaultdict(lambda: 0.0)
        for symptomCode, trList in self.symptomCodeToTimeRanges.iteritems():
            symptomCodeToTime[symptomCode] = sum(tr.absTime() for tr in trList)
        totalTime = sum(symptomCodeToTime.values())
        assert(abs(totalTime - self.timeRange.absTime()) < 1E-3)
        return symptomCodeToTime

    ############################
    def setTimes(self):
        self.symptomCodeToTimeRanges = defaultdict(list)
        self.symptomCategoryToTimeRanges = defaultdict(list)
        for s in self.statuses:
            st = s['time']
            tr = TimeRange(s['time'], s.get('end_time',st))
            sc = s['symptom_code']
            c = s['symptomCategory']
            self.symptomCodeToTimeRanges[sc].append(tr)
            self.symptomCategoryToTimeRanges[c].append(tr)
        self.symptomCategoryToTime = self.getTimeAllocation()
        self.symptomCategoryToAbsTime = self.getAbsTimeAllocation()
        self.symptomCodeToTime = self.getSymptomTimeAllocation()
        self.symptomCodeToAbsTime = self.getSymptomAbsTimeAllocation()
