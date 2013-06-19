#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import bottle
import pymongo
from StringIO import StringIO
from datetime import datetime
from operator import itemgetter
from collections import defaultdict, Counter

import hotCars
import dbUtils
import metroEscalatorsWeb
import hotCarsWeb
import stations

#bottle.debug(True)

REPO_DIR = os.environ['OPENSHIFT_REPO_DIR']
STATIC_DIR = os.path.join(REPO_DIR, 'wsgi', 'static')
bottle.TEMPLATE_PATH.append(os.path.join(REPO_DIR, 'wsgi', 'views'))

########################################
@bottle.route('/')
def index():
    bottle.redirect('/stations')

########################################
@bottle.route('/hotcars')
def allHotCars():
    hotCarData = hotCarsWeb.getHotCarData()
    return bottle.template('hotCars', hotCarData=hotCarData)

########################################
from bottle import static_file
@bottle.route('/static/<filename>')
def server_static(filename):
    return static_file(filename, root=STATIC_DIR)

########################################
@bottle.route('/escalators/<unitId>')
def escalatorStatus(unitId):
    if len(unitId) == 6:
        unitId = '%sESCALATOR'%unitId
    db = dbUtils.getDB()
    escId = dbUtils.unitToEscId.get(unitId, None)
    if escId is None:
        return 'No escalator found'
    statuses = dbUtils.getEscalatorStatuses(escId = escId)
    dbUtils.addStatusAttr(statuses)

    curTime = datetime.now()
    # Set the end_time of the current status to now
    if statuses and 'end_time' not in statuses[0]:
        statuses[0]['end_time'] = curTime


    escData = dbUtils.escIdToEscData[escId]

    # Summarize the escalator performance
    startTime = datetime(2000,1,1)
    escSummary = dbUtils.summarizeStatuses(statuses, startTime=startTime, endTime=datetime.now())
    return bottle.template('escalator', unitId = unitId[0:6], escData=escData, statuses=statuses,
                           escSummary=escSummary)

###############################################
@bottle.route('/stations/<shortName>')
def stationStatus(shortName):

    # Get the station code
    codes = [c for c,sn in stations.codeToShortName.iteritems() if sn==shortName]
    if not codes:
        return 'No station found'
    stationCode = codes[0]

    # Get the summary for this station over all time
    stationSummary = dbUtils.getStationSummary(stationCode)

    # Get the current overview of escalators in this station
    stationSnapshot = dbUtils.getStationSnapshot(stationCode)
    escUnitIds = stationSummary['escUnitIds']
    escToSummary = stationSummary['escToSummary']
    escToStatuses = stationSummary['escToStatuses']

    # Generate the table listing of escalators
    escalatorListing = []
    for escUnitId in escUnitIds:
        escSummary = escToSummary.get(escUnitId, {})
        statuses = escToStatuses[escUnitId]
        if not statuses:
            continue
        latestStatus = statuses[0]
        escId = dbUtils.unitToEscId[escUnitId]
        escMetaData = dbUtils.escIdToEscData[escId]
        shortUnitId = escUnitId[0:6]
        rec = {'unitId' : shortUnitId,
               'stationDesc' : escMetaData['station_desc'],
               'escDesc' : escMetaData['esc_desc'],
               'curStatus' : latestStatus['symptom'],
               'curSymptomCategory' : latestStatus['symptomCategory'],
               'availability' : escSummary['availability']} 
        escalatorListing.append(rec)

    escalatorListing = sorted(escalatorListing, key = itemgetter('unitId'))
    return bottle.template('station', stationSummary=stationSummary,
        stationSnapshot=stationSnapshot, escalators=escalatorListing)

###############################################
@bottle.route('/escalators')
def allEscalators():
    escalatorList = metroEscalatorsWeb.escalatorList()

    # Group escalators by station
    stationToEsc = defaultdict(list)
    for esc in escalatorList:
        stationToEsc[esc['stationName']].append(esc)

    # Sort each escalators stations in ascending order by code
    for k,escList in stationToEsc.iteritems():
        stationToEsc[k] = sorted(escList, key = itemgetter('unitId'))

    return bottle.template('escalators', stationToEsc=stationToEsc)

###############################################
@bottle.route('/escalators/nonoperational')
def nonoperationalEscalators():

    escalatorList = metroEscalatorsWeb.escalatorNotOperatingList()

    # Summarize the non-operational escalators by symptom
    symptomCounts = Counter(esc['symptom'] for esc in escalatorList)

    # Get the availability and weighted availability
    systemAvailability = dbUtils.getSystemAvailability()
    return bottle.template('escalatorsNonoperational', escList=escalatorList, symptomCounts=symptomCounts, systemAvailability=systemAvailability)

###############################################
@bottle.route('/escalators/rankings')
def escalatorRankings():
    rankingDict = metroEscalatorsWeb.getRankings()
    compiledRankings = metroEscalatorsWeb.compileRankings(rankingDict)
    return bottle.template('escalatorRankings', rankings=compiledRankings)

###############################################
@bottle.route('/stations')
# Listing of all stations
def stationListing():
    stationRecs = metroEscalatorsWeb.stationList()
    return bottle.template('stations', stationRecs=stationRecs)


application = bottle.default_app()
