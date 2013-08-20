#!/usr/bin/env python
# Export data into json and csv formats.
# This is used for sharing the data publicly on the DC MetroMetrics website.
################################

import os, sys
from operator import itemgetter
from dateutil import tz
from copy import deepcopy
import json

# Add the REPO_DIR to sys.path
REPO_DIR = os.environ['OPENSHIFT_REPO_DIR']
sys.path.append(REPO_DIR)

from dcmetrometrics.common import dbGlobals
from dcmetrometrics.eles import dbUtils
from dcmetrometrics.common.metroTimes import toUtc
from dcmetrometrics.hotcars.hotCars import getAllHotCarReports

dbg = dbGlobals.DBGlobals()
db = dbg.getDB()

DATA_DIR = os.environ['OPENSHIFT_DATA_DIR']
SHARED_DATA_DIR = os.path.join(DATA_DIR, 'shared')
if not os.path.exists(SHARED_DATA_DIR):
    os.mkdir(SHARED_DATA_DIR)

HOT_CAR_JSON = os.path.join(SHARED_DATA_DIR, 'hotcars.json')
HOT_CAR_CSV = os.path.join(SHARED_DATA_DIR, 'hotcars.csv')
ESCALATOR_JSON = os.path.join(SHARED_DATA_DIR, 'escalators.json')
ESCALATOR_DESCRIPTION_CSV = os.path.join(SHARED_DATA_DIR, 'escalator_descriptions.csv')
ESCALATOR_STATUSES_CSV = os.path.join(SHARED_DATA_DIR, 'escalator_statuses.csv')

# Export hot car data to 'hotcars.json' 
def exportHotCarData():
    hotCarToReports = getAllHotCarReports(db)
    allReports = sorted([r for rl in hotCarToReports.itervalues() for r in rl], key=itemgetter('time'))
    keys = ['user_id', 'color', 'text', 'car_number', 'tweet_id', 'time', 'handle']

    keys_old = ['time', 'car_number', 'color', 'tweet_id', 'user_id']
    keys_new = ['time', 'car_number', 'color', 'tweet_id', 'twitter_user_id']
    keys_old2new = dict(zip(keys_old, keys_new))
    keys_new2old = dict(zip(keys_new, keys_old))

    def makeDict(d):
        newd = dict((keys_old2new[k], d[k]) for k in keys_old)
        utcTime = toUtc(d['time'])
        newd['time'] = utcTime.isoformat()
        return newd

    allReports = [makeDict(r) for r in allReports]

    # Export JSON
    fout = open(HOT_CAR_JSON, 'w')
    json.dump(allReports, fout)
    fout.close()

    # EXPORT CSV
    fout = open(HOT_CAR_CSV, 'w')
    fout.write(','.join(keys_new) + '\n')
    for r in allReports:
        outS = ','.join(str(r[k]) for k in keys_new)
        fout.write('%s\n'%outS)
    fout.close()
    return allReports

#################################
# Export all escalator statuses
def exportEscalatorData():
    escIds = dbg.getEscalatorIds()
    escIdToStatuses = {}
    for escId in escIds:
        escIdToStatuses[escId] = dbUtils.getEscalatorStatuses(escId)

    escDataKeys_old = ['esc_desc', 'station_code', 'station_desc', 'station_name', 'unit_id']
    escDataKeys_new = ['escalator_description', 'station_code', 'station_description', 'station_name', 'unit_id']
    statusDataKeys_old = ['symptom', 'symptomCategory', 'symptom_code', 'tickDelta', 'time']
    statusDataKeys_new = ['symptom', 'symptom_category', 'symptom_code', 'tick_delta', 'start_time']

    def getEscalatorData(status):
        escData = dict((k2, status[k1]) for k1,k2 in zip(escDataKeys_old, escDataKeys_new))
        return escData

    def getStatusData(status):
        statusData = dict((k2, status[k1]) for k1,k2 in zip(statusDataKeys_old, statusDataKeys_new))
        return statusData

    escUnitIdToData = {}
    for escId, statuses in escIdToStatuses.iteritems():
        if not statuses:
            continue
        escData = getEscalatorData(statuses[0])
        statusData = [getStatusData(s) for s in statuses] # sorted in descending order

        # Set the end_time and duration fields for statuses
        for s2,s1 in zip(statusData[0:-1], statusData[1:]):
            s1['end_time'] = s2['start_time']
            s1['duration'] = (s1['end_time'] - s1['start_time']).total_seconds()

        for s in statusData:
            s['start_time'] = s['start_time'].isoformat()
            if 'end_time' in s:
                s['end_time'] = s['end_time'].isoformat()

        d = {'description' : escData,
             'statuses' : statusData}
        escUnitIdToData[escData['unit_id']] = d

    # Export JSON
    fout = open(ESCALATOR_JSON, 'w')
    json.dump(escUnitIdToData, fout)
    fout.close()

    # Build data for CSV export
    escUnitNames = sorted(escUnitIdToData.keys())
    escDescriptions = [escUnitIdToData[k]['description'] for k in escUnitNames]
    escDescriptions = sorted(escDescriptions, key = itemgetter('unit_id'))
    escDataKeys_csv = ['unit_id', 'station_name', 'station_code', 'station_description', 'escalator_description']
    escStatusKeys_csv = ['unit_id', 'start_time', 'end_time', 'duration', 'symptom', 'symptom_category', 'symptom_code']

    # Build the list of csv statuses
    csvStatuses = []
    for escUnitName in escUnitNames:
        statuses = escUnitIdToData[escUnitName]['statuses']
        for s in statuses:
            s = deepcopy(s)
            for k,v in s.iteritems():
                s[k] = str(v)
            s['unit_id'] = escUnitName
            if 'duration' not in s:
                s['duration'] = ''
            if 'end_time' not in s:
                s['end_time'] = ''
            csvStatuses.append(s) 

    def descriptionToCsvString(d):
        fields = [d[k].replace(',',' ') for k in escDataKeys_csv]
        return ','.join(fields)

    def statusToCsvString(d):
        fields = [d[k].replace(',',' ') for k in escStatusKeys_csv]
        return ','.join(fields)
    
    # Write ESCALATOR_DESCRIPTION_CSV
    fout = open(ESCALATOR_DESCRIPTION_CSV, 'w')
    fout.write(','.join(escDataKeys_csv) + '\n') # header line
    for d in escDescriptions:
        fout.write(descriptionToCsvString(d) + '\n')
    fout.close()

    # Write ESCALATOR_STATUSES_CSV
    fout = open(ESCALATOR_STATUSES_CSV, 'w')
    fout.write(','.join(escStatusKeys_csv) + '\n') # header line
    for d in csvStatuses:
        fout.write(statusToCsvString(d) + '\n')
    fout.close()

    return escUnitIdToData

def run():
    exportHotCarData()
    exportEscalatorData()

if __name__ == "__main__":
    run()
