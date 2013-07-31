# python modules
import os
import sys
from time import sleep
from datetime import datetime, date, time, timedelta
from metroTimes import utcnow, tzutc, metroIsOpen, toLocalTime

# Custom modules
import stations
from incident import Incident
from twitter import TwitterError
import dbUtils
from dbUtils import invDict, getDB
import utils
import twitterUtils
from escalatorRequest import getELESIncidents, WMATA_API_ERROR
from utils import *
from keys import MetroEscalatorKeys
from escalatorDefs import symptomToCategory, OPERATIONAL_CODE
import metroEscalatorsWeb
from ELESApp import ELESApp

#############################################
# Get escalator incidents
def getEscalatorIncidents(log=sys.stdout):
    escIncidents = getELESIncidents()['incidents'] # This will throw an exception
                                                   # if the request fails
    escIncidents = [i for i in escIncidents if i.isEscalator()]
    return escIncidents

#############################################
class EscalatorApp(ELESApp):
    
    def __init__(self, log, LIVE=True, QUIET=False):
        ELESApp.__init__(self, log, LIVE, QUIET)

    def getIncidents(self):
        return getEscalatorIncidents(log=self.log)

    def getLatestStatuses(self):
        return dbUtils.getLatestStatuses(escalators=True)

    def getAppStateCollection(self):
        db = dbUtils.getDB()
        return db.escalator_appstate

    def getStatusesCollection(self):
        db = dbUtils.getDB()
        return db.escalator_statuses

    # Trigger webpage regeneration when an escalator changes status
    def statusUpdateCallback(self, doc):
        db = dbUtils.getDB()
        escId = doc['escalator_id']

        # Mark webpages for regeneration
        update = {'$set' : {'forceUpdate':True}}
        escData = dbUtils.escIdToEscData[escId]
        stationCode = escData['station_code']
        stationShortName = stations.codeToShortName[stationCode]
        escId = doc['escalator_id']

        db.webpages.update({'class' : 'escalator', 'escalator_id' : escId}, update)
        db.webpages.update({'class' : 'escalatorDirectory'}, update)
        db.webpages.update({'class' : 'escalatorOutages'}, update)
        db.webpages.update({'class' : 'stationDirectory'}, update)
        db.webpages.update({'class' : 'station', 'station_name' : stationShortName}, update)

    def getTwitterKeys(self):
        return MetroEscalatorKeys

    def getTweetOutbox(self):
        db = dbUtils.getDB()
        return db.escalator_tweet_outbox

    def runDailyStats(self, curTime):
        db = dbUtils.getDB()
        curTimeLocal = toLocalTime(curTime)
        appState = db.escalator_appstate.find_one()
        lastStatsTime = None
        if appState is not None:
            lastStatsTime = appState.get('lastDailyStatsTime', None)
            if lastStatsTime:
                lastStatsTime = lastStatsTime.replace(tzinfo=tzutc)
        lastRanDay = toLocalTime(lastStatsTime).weekday() if lastStatsTime else None

        # Send the daily stats at 8 AM
        runStats = (curTimeLocal.hour >= 8 and curTimeLocal.hour <= 9)
        runStats = runStats and ((lastRanDay is None) or (lastRanDay != curTimeLocal.weekday()))

        # If we do not need to run the dailyStats, return
        if not runStats:
            return

        dailyStatsMsg = dailyStats(curTime, startTime = lastStatsTime)
        if dailyStatsMsg is not None:
            self.storeTweets([dailyStatsMsg])

        update = {'$set' : {'lastDailyStatsTime' : curTime}}
        db.escalator_appstate.update({'_id' : 1}, update, upsert = True)

    # Return a str with escalator availability information.
    @staticmethod
    def availabilityMaker(escId):
        availabilityData = dbUtils.getSystemAvailability(escalators=True)
        escData = dbUtils.getEsc(escId)
        stationCode = escData['station_code']
        sAvail = availabilityData['stationToAvailability'][stationCode]
        aStr = 'A=%.1f%%'%(100.0*availabilityData['availability'])
        sAstr = 'sA=%.1f%%'%(100.0*sAvail)
        return '%s %s'%(aStr, sAstr)

    # Return a str with the url for the escalator.
    @staticmethod
    def urlMaker(escId):
        unit = dbUtils.escIdToUnit[escId][0:6]
        escUrl = metroEscalatorsWeb.escUnitIdToAbsWebPath(unit)
        return escUrl

#######################################
# Compute the daily stats for the last 24 hour
def dailyStats(curTime, startTime = None):
    
    escIdToSummary = {}
    # Generate a summary for each escalator
    if startTime is None:
        startTime = curTime - timedelta(hours=24.0)
    endTime = curTime

    escIds = dbUtils.getEscalatorIds()
    for escId in escIds:

        # Retrieve data for this escalator and its station
        escData = dbUtils.escIdToEscData[escId]
        stationCode = escData['station_code']
        stationData = stations.codeToStationData[stationCode]

        # Retrieve the latest statuses
        statuses = dbUtils.getEscalatorStatuses(escId = escId, startTime = startTime, endTime = endTime)

        # Summarize the statuses
        summary = dbUtils.summarizeStatuses(statuses, startTime=startTime, endTime=endTime)
        summary['escId'] = escId
        summary['stationCode'] = stationCode
        summary['escalatorWeight'] = stationData['escalatorWeight']
        escIdToSummary[escId] = summary

    numBreaks = sum(s.get('numBreaks', 0) for s in escIdToSummary.itervalues())
    numFixes = sum(s.get('numFixes', 0) for s in escIdToSummary.itervalues())
    numInspections = sum(s.get('numInspections', 0) for s in escIdToSummary.itervalues())

    summaries = escIdToSummary.itervalues
    availabilities = [s['availability'] for s in summaries()]
    availability = sum(availabilities)/float(len(availabilities))

    # Compute weighted availability
    denom = float(sum(s['escalatorWeight'] for s in summaries()))
    wAvailability = sum(s['escalatorWeight']*s['availability'] for s in summaries())/denom

    msg = 'Good Morning DC! #WMATA Escalator #DailyStats: Breaks=%i Fixes=%i Inspections=%i A=%.2f%% wA=%.2f%%' % \
          (numBreaks, numFixes, numInspections, 100.0*availability, 100.0*wAvailability)

    return msg
