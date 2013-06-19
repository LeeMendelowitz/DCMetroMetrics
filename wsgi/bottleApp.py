#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import bottle
import pymongo
from StringIO import StringIO
from datetime import datetime
from operator import itemgetter

import hotCars
import dbUtils
import metroEscalatorsWeb
import stations

bottle.debug(True)

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
    db = dbUtils.getDB()
    hotCarDict = hotCars.getAllHotCarReports(db)
    return bottle.template('hotCars', hotCarDict=hotCarDict)

########################################
from bottle import static_file
@bottle.route('/static/<filename>')
def server_static(filename):
    return static_file(filename, root=STATIC_DIR)

########################################
@bottle.route('/escalators/<unitId>')
def printEscalatorStatus(unitId):
    if len(unitId) == 6:
        unitId = '%sESCALATOR'%unitId
    db = dbUtils.getDB()
    escId = dbUtils.unitToEscId.get(unitId, None)
    if escId is None:
        return 'No escalator found'
    statuses = dbUtils.getEscalatorStatuses(escId = escId)
    dbUtils.addStatusAttr(statuses)
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
    return bottle.template('escalators', escalators=escalatorList)


###############################################
@bottle.route('/stations')
# Listing of all stations
def stationListing():
    stationRecs = metroEscalatorsWeb.stationList()
    return bottle.template('stations', stationRecs=stationRecs)


application = bottle.default_app()
