# Utilities for interacting with a MongoDB
# Functionality for updating the databases
import pymongo
import sys
import os
from collections import defaultdict
from datetime import timedelta

invDict = lambda d: dict((v,k) for k,v in d.iteritems())

OPERATIONAL_CODE = -1

###############################
def getDB():
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
    addSymptomCode(db, OPERATIONAL_CODE, 'OPERATIONAL')
    return db

########################################
# Create dictionary from escalator unit id
# to the pymongo id
def getUnitToId(db):
    escList = list(db.escalators.find())
    unitToId = dict((d['unit_id'],d['_id']) for d in escList)
    return unitToId

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
    query = {'_id' : 1}
    update = {}
    if lastRunTime is not None:
        update['lastRunTime'] = lastRunTime
    if nextDailyStatsTime is not None:
        update['nextDailyStatsTime'] = nextDailyStatusTime
    if not update:
        return
    db.app_state.find_and_modify(query=query, update=update, upsert=True)

########################################
# Initialize the escalator databased with entries
# Initialize the escalator_statuses database with default
# OPERATIONAL entries
def initializeEscalators(db, escDataList, curTime):
    addSymptomCode(db, OPERATIONAL_CODE, 'OPERATIONAL')
    for d in escDataList:
        addEscalator(db, curTime, d['unit_id'], d['station_code'],
                         d['station_name'], d['esc_desc'],
                         d.get('station_desc',None))

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
        operational_code = symptomToId['OPERATIONAL']
        doc = {'escalator_id' : escId,
               'time' : curTime - timedelta(milliseconds=1),
               'tickDelta' : 0,
               'symptom_code' : operational_code}
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

##########################################################
# For each escalator, retrieve the latest status updates.
def getLatestStatuses(db):

    # Get the unique escalator ids
    esc_ids = db.escalator_statuses.distinct('escalator_id')

    db.escalator_statuses.ensure_index([('escalator_id', pymongo.ASCENDING),
                                        ('time', pymongo.DESCENDING)])

    unitToId = getUnitToId(db)
    escIdToUnit = invDict(unitToId)
    symptomToId = getSymptomToId(db)
    operational_code = symptomToId['OPERATIONAL']
    symptomCodeToSymptom = invDict(symptomToId)
    docToStr = lambda d: doc2Str(d, escIdToUnit, symptomCodeToSymptom)

    last_status = {}

    for esc_id in esc_ids:

        # Find latest 1000 statuses for this escalator
        sort_params = [('time', pymongo.DESCENDING)]
        cursor = db.escalator_statuses.find({'escalator_id' : esc_id}, sort=sort_params)
        latest = getSome(cursor, 1000) # Latest status updates for this escalator

        ###########################
#        # DEBUG
#        sys.stdout.write('\n\n\n' + '*'*50 + '\n')
#        sys.stdout.write('Latest Status for escalator %s\n'%escIdToUnit[esc_id])
#        for doc in latest:
#            sys.stdout.write('%s\n'%docToStr(doc))
#        sys.stdout.write('*'*50+'\n\n\n')
        ###########################


        last_update = latest[0] if latest else None

        # Get the latest status where escalator was operating
        query = (rec for rec in latest if rec['symptom_code'] == operational_code)
        last_operational = getOne(query)
        last_operational_time = last_operational['time'] if last_operational is not None else None

        # Find the earliest break status since the last operational status
        # Most recent break status
        last_break = None
        if last_operational is not None:
            query = [rec for rec in latest if rec['symptom_code'] != operational_code and rec['time'] > last_operational_time]
            last_break = query[-1] if query else None

        last_status[esc_id] = {'last_update' : last_update,
                               'last_operational' : last_operational,
                               'last_break' : last_break}
    return last_status


def doc2Str(doc, escIdToUnit, symptomCodeToSymptom):  
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
# Return a dictionary with escalators that have changed status
# Key are escalator ids
# Value is dictionary with keys: ['cur_update', 'last_update', 'last_operational', 'last_break']
def processIncidents(db, curIncidents, curTime, tickDelta):

    sys.stdout.write('dbUtils.processIncidents: Processing %i incidents\n'%len(curIncidents))
    sys.stdout.write('escalator_statuses has %i documents\n'%(db.escalator_statuses.find().count()))
    sys.stdout.flush()
    for inc in curIncidents:
        updateDBFromIncidentData(db, inc, curTime)

    unitToId = getUnitToId(db)
    escIdToUnit = invDict(unitToId)
    symptomToId = getSymptomToId(db)
    symptomCodeToSymptom = invDict(symptomToId)
    operational_code = symptomToId['OPERATIONAL']

    # Create dictionary of escalator to the current status
    escIdToCurStatus = defaultdict(lambda: operational_code)
    incStatus = lambda inc: (unitToId[inc.UnitId], symptomToId[inc.SymptomDescription])
    escIdToCurStatus.update(incStatus(inc) for inc in curIncidents)

    # Get the last known statuses for all escalators.
    # Recast escStatuses as a defaultdict
    escStatusItems = getLatestStatuses(db).items()
    default_entry = {'last_update' : None,
                     'last_operational' : None,
                     'last_break' : None}
    escStatuses = defaultdict(lambda: default_entry)
    escStatuses.update(escStatusItems)
    escIdToLastStatus = defaultdict(lambda: operational_code)
    escIdToLastStatus.update((escId, escStatus['last_update']['symptom_code']) for
                              escId, escStatus in escStatuses.iteritems())

    #### DEBUG #########################
#    docToStr = lambda d: doc2Str(d, escIdToUnit, symptomCodeToSymptom)
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
        changedStatusData['cur_update'] = doc
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
#        docToStr = lambda d: doc2Str(d, escIdToUnit, symptomCodeToSymptom)
#        for doc in docs:
#            sys.stderr.write('%s\n'%docToStr(doc))
#        sys.stderr.write('-'*50 + '\n\n')
#        ####
    return changedStatusDict
