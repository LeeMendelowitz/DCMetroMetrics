"""
eles.escalator

Define the EscalatorApp class, which is reponsible for
querying the WMATA API for escalator outages, storing outages
in a database, and generating tweets for the @MetroEscalator
twitter app.

"""

# python modules
import os
import sys
from time import sleep
from datetime import datetime, date, time, timedelta

# TEST CODE
if __name__ == '__main__':
    #import dcmetrometrics.test.setup
    from ..test import setup

# Custom modules
from ..common import dbGlobals, twitterUtils, utils, stations
from ..common.metroTimes import toLocalTime, tzutc
from ..common.globals import DATA_DIR
from ..third_party.twitter import TwitterError
from . import dbUtils
from .dbUtils import invDict
from ..keys import MetroEscalatorKeys
from .Incident import Incident
from .defs import symptomToCategory, OPERATIONAL_CODE as OP_CODE, NUM_ESCALATORS
from .ELESApp import ELESApp, getELESIncidents
from ..web import eles as elesWeb

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

    def initDB(self, db, curTime):

        # Add the operational code
        db.symptom_codes.update({'_id' : OP_CODE},
                                {'$set' : {'symptom_desc' : 'OPERATIONAL'}},
                                upsert=True)

        # Initialize the escalator/elevator database if necessary
        escalators = self.dbg.getEscalatorIds()
        numEscalators = len(escalators)

        if numEscalators < NUM_ESCALATORS:
            escalatorTsv = os.path.join(DATA_DIR, 'escalators.tsv')
            escData = utils.readEscalatorTsv(escalatorTsv)
            for d in escData:
                d['unit_type'] = 'ESCALATOR'
            assert(len(escData) == NUM_ESCALATORS)
            dbUtils.initializeEscalators(db, escData, curTime)

        self.dbg.update()

    def getIncidents(self):
        return getEscalatorIncidents(log=self.log)

    def getLatestStatuses(self):
        return dbUtils.getLatestStatuses(escalators=True, dbg=self.dbg)

    def getAppStateCollection(self):
        return self.db.escalator_appstate

    def getStatusesCollection(self):
        return self.db.escalator_statuses

    # Trigger webpage regeneration when an escalator changes status
    def statusUpdateCallback(self, doc):
        db = self.db
        escId = doc['escalator_id']

        # Mark webpages for regeneration
        update = {'$set' : {'forceUpdate':True}}
        escData = self.dbg.escIdToEscData[escId]
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
        return self.db.escalator_tweet_outbox

    def runDailyStats(self, curTime):
        db = self.db
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

        dailyStatsMsg = self.dailyStats(curTime)
        if dailyStatsMsg is not None:
            self.storeTweets([dailyStatsMsg])

        update = {'$set' : {'lastDailyStatsTime' : curTime}}
        db.escalator_appstate.update({'_id' : 1}, update, upsert = True)

    # Return a str with escalator availability information.
    def availabilityMaker(self, escId):
        availabilityData = dbUtils.getSystemAvailability(escalators=True, dbg=self.dbg)

        escData = self.db.escalators.find_one({"_id" : escId})
        if escData is None:
            raise RuntimeError("Could not find escalator in db.escalators with id %s"%str(escId))

        stationCode = escData['station_code']
        sAvail = availabilityData['stationToAvailability'][stationCode]
        aStr = 'A=%.1f%%'%(100.0*availabilityData['availability'])
        sAstr = 'sA=%.1f%%'%(100.0*sAvail)
        return '%s %s'%(aStr, sAstr)

    # Return a str with the url for the escalator.
    def urlMaker(self, escId):
        unit = self.dbg.escIdToUnit[escId][0:6]
        escUrl = elesWeb.escUnitIdToAbsWebPath(unit)
        return escUrl

    #######################################
    # Compute the daily stats for the last 24 hour
    def dailyStats(self, curTime, startTime = None):
        
        escIdToSummary = {}
        # Generate a summary for each escalator
        if startTime is None:
            startTime = curTime - timedelta(hours=24.0)
        endTime = curTime

        escIds = self.dbg.getEscalatorIds()
        for escId in escIds:

            # Retrieve data for this escalator and its station
            escData = self.dbg.escIdToEscData[escId]
            stationCode = escData['station_code']
            stationData = stations.codeToStationData[stationCode]

            # Retrieve the latest statuses
            statuses = dbUtils.getEscalatorStatuses(escId = escId, startTime = startTime, endTime = endTime, dbg=self.dbg)

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


# TEST CODE
if __name__ == "__main__":
    import time
    import sys
    app = EscalatorApp(log=sys.stdout, LIVE=False)
    while True:
        msg = '*'*50 + '\nTEST TICK:\n'
        sys.stdout.write(msg)
        app.tick()
        time.sleep(10)
