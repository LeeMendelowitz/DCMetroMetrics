# Create a list of phony incidents to test populating the database
import os
import test_setup
from incident import Incident
from datetime import datetime, timedelta
from collections import defaultdict
import dbUtils

test_setup.setupPaths()

DATA_DIR = os.environ['OPENSHIFT_DATA_DIR']
TEST_DATA_DIR = os.path.join(DATA_DIR, 'test_data')

testDataFile = os.path.join(TEST_DATA_DIR, 'data.tsv')
OPERATIONAL_CODE = -1

def readTestData(tsvFile):
    fin = open(tsvFile)
    fin.next()
    incFields = ['UnitName', 'UnitType', 'StationCode',
              'StationName', 'LocationDescription', 'SymptomCode',
              'SymptomDescription']
    otherFields = ['Group']
    allFields = incFields + otherFields
    data = []
    for l in fin:
        fieldVals = l.strip().split('\t')
        assert(len(fieldVals) == len(allFields))
        nIncFields = len(incFields)
        incFieldVals = fieldVals[:nIncFields]
        oFieldVals = fieldVals[nIncFields:]
        incData = dict(zip(incFields, incFieldVals))
        group = int(oFieldVals[0])
        data.append((incData,group))
    return data


def getTestData():
    data = readTestData(testDataFile)
    groupToData = defaultdict(list)
    for d,group in data:
        groupToData[group].append(Incident(d))
    groupKeys = sorted(groupToData.keys())
    tdelta = timedelta(seconds=30) # seconds
    n = datetime.now()
    startTime = n - len(groupKeys)*tdelta
    
    res = []
    for i,k in enumerate(groupKeys):
        incidents = groupToData[k]
        tickDelta = tdelta.seconds
        curTime = startTime + i*tdelta
        res.append([incidents, curTime, tickDelta])

    return res

def runTest(db):
    testData = getTestData()
    for incList, curTime, tickDelta in testData:
        res = dbUtils.processIncidents(db, incList, curTime, tickDelta)

def run():
    try:
        test_setup.startup()
        db = test_setup.getDB()
        dbUtils.addSymptomCode(db, OPERATIONAL_CODE, 'OPERATIONAL')
        runTest(db)
        test_setup.shutdown()
    except:
        test_setup.shutdown()

if __name__ == '__main__':
    run()
