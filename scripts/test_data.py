# Create a list of phony incidents to test populating the database
import os
import sys
import test_setup
from incident import Incident
from datetime import datetime, timedelta
from collections import defaultdict
import dbUtils
import time
import twitterApp
import twitterApp
from twitterApp import TwitterApp

test_setup.setupPaths()

DATA_DIR = os.environ['OPENSHIFT_DATA_DIR']
TEST_DATA_DIR = os.path.join(DATA_DIR, 'test_data')

testDataFile = os.path.join(TEST_DATA_DIR, 'data.tsv')

def readTestData(tsvFile):
    fin = open(tsvFile)
    fin.next()
    incFields = ['UnitName', 'UnitType', 'StationCode',
              'StationName', 'LocationDescription', 'SymptomCode',
              'SymptomDescription']
    otherFields = ['offset']
    allFields = incFields + otherFields
    numFields = len(allFields)
    data = []
    for l in fin:
        fieldVals = l.strip().split('\t')
        fieldVals = fieldVals[0:numFields]
#        assert(len(fieldVals) == len(allFields))
        nIncFields = len(incFields)
        incFieldVals = fieldVals[:nIncFields]
        oFieldVals = fieldVals[nIncFields:]
        incData = dict(zip(incFields, incFieldVals))
        offset = int(oFieldVals[0])
        data.append((incData,offset))
    return data


def getTestData():
    data = readTestData(testDataFile)
    groupToData = defaultdict(list)
    for d,group in data:
        groupToData[group].append(Incident(d))
    groupKeys = sorted(groupToData.keys())
    oneSec = timedelta(seconds=1) # 1 second
    startTime = datetime(2013, 1, 1, 12, 0, 0)
    
    res = []
    for i, offset in enumerate(groupKeys):
        incidents = groupToData[offset]
        offset_delta = offset*oneSec
        curTime = startTime + offset_delta
        res.append([curTime, incidents])

    return res

def printUpdates(db, updateDict):
    unitToId = dbUtils.getUnitToId(db)
    symptomToId = dbUtils.getSymptomToId(db)
    invDict = lambda d: dict((v,k) for k,v in d.iteritems())
    escIdToUnit = invDict(unitToId)
    symptomIdToDesc = invDict(symptomToId)

    sys.stdout.write("Generated %i updates:\n"%len(updateDict))
    for escId, statusData in updateDict.iteritems():
        escName = escIdToUnit[escId]
        lastUpdate = statusData['last_update']
        curUpdate = statusData['cur_update']
        oldStatus = lastUpdate['symptom_code'] if lastUpdate is not None else 'None'
        curStatus = str(curUpdate['symptom_code'])
        sys.stdout.write('Unit %s from %s to %s.\n'%(escName, oldStatus, curStatus))


def runTest(db):
    testData = getTestData()
    log = sys.stdout
    T = TwitterApp(log, LIVE=False)
    db = dbUtils.getDB()

    # Clear out the databases
    db.escalator_appstate.remove()
    db.escalators.remove()
    db.escalator_statuses.remove()
    db.symptom_codes.remove()
    db.escalator_tweet_outbox.remove()

    # Initialize the databases
    #now = datetime.now()
    now = datetime(2013, 1, 1, 12, 0, 0)
    twitterApp.initDB(db, curTime=now)

    for curTime, incList in testData:
        #res = dbUtils.processIncidents(db, incList, curTime, tickDelta)
        sys.stdout.write('*'*50 + '\nRunning tick:\n\n')
        T.runTick(db, curTime, incList, log=log)

def run():
    test_setup.startup()
    db = test_setup.getDB()
    runTest(db)
    test_setup.shutdown()

if __name__ == '__main__':
    run()
