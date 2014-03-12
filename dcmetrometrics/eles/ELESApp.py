"""
eles.ELESApp

Base class for EscalatorApp and ElevatorApp, which 
drive MetroEscalators and MetroElevators
"""

# python modules
import os
import sys
from time import sleep
from datetime import datetime, date, time, timedelta
from collections import defaultdict

# Custom modules
from ..common import dbGlobals, twitterUtils, utils, stations
from ..common.metroTimes import utcnow, tzutc, metroIsOpen, toLocalTime, isNaive
from ..common.globals import DATA_DIR
import dbUtils
from .dbUtils import invDict
from ..keys import WMATA_API_KEY
from ..third_party.twitter import TwitterError
from .Incident import Incident
from .WMATA_API import WMATA_API_ERROR, WMATA_API
from .defs import symptomToCategory, OPERATIONAL_CODE as OP_CODE

TWEET_LEN = 140

# Silence tweeting if the tick delay is greater than 20 minutes
SILENCE_GAP = 60*20

# Maximum number of tweets allowed in a single tick. Otherwise
# the tick is silenced
MAX_TICK_TWEETS = 10

OUTPUT_DIR = DATA_DIR
if OUTPUT_DIR is None:
    OUTPUT_DIR = os.getcwd()

def checkWMATAKey():
    """
    Check that the WMATA_API_KEY has been properly set.
    """
    if WMATA_API_KEY is None:
        msg = \
        """

        WMATA_API_KEY is required for the Elevator App and Escalator App.
        Check your keys.py

        For more information, see:
        https://github.com/LeeMendelowitz/DCMetroMetrics/wiki/API-Keys

        """
        from ..keys import MissingKeyError
        raise MissingKeyError(msg)

    if not isinstance(WMATA_API_KEY,str):
        raise TypeError('WMATA_API_KEY must be a str. Check your keys.py')

def getELESIncidents():
    """
    Get all escalator/elevator incidents from the WMATA API.
    This requires a valid WMATA API key
    """
    checkWMATAKey()
    api = WMATA_API(key=WMATA_API_KEY)
    res = api.getEscalator()
    incidents = res.json()['ElevatorIncidents']
    incidents = [Incident(i) for i in incidents]
    result = { 'incidents' : incidents,
               'requestTime' : datetime.now() }
    return result

#############################################
class ELESApp(object):
    """
    Base class for ElevatorApp and EscalatorApp
    """
    
    def __init__(self, log, LIVE=True, QUIET=False):
        self.LIVE = LIVE
        self.QUIET = QUIET
        self.twitterApi = None

        # Check if the Twitter Keys have been set.
        self.twitterKeys = self.getTwitterKeys()
        if not self.twitterKeys.isSet():
            self.LIVE = False

        # Require that the WMATA Key is set.
        self.checkWMATAKey()

        self.log = log
        self.dbg = dbGlobals.DBGlobals()
        self.db = self.dbg.getDB()

    #####################################
    # Methods which should be implemented by child
    def initDB(self, db, curTime):
        raise NotImplementedError()

    def getIncidents(self):
        raise NotImplementedError()

    def getAppStateCollection(self):
        raise NotImplementedError()

    def getTwitterKeys(self):
        raise NotImplementedError()

    # Wrap a call to dbUtils.getLatestStatuses
    def getLatestStatuses(self):
        raise NotImplementedError()

    def getTweetOutbox(self):
        raise NotImplementedError()

    # Callback to be called on each document which is added to the 
    # statuses collection. This callback can be used to trigger
    # web page regenerations.
    def statusUpdateCallback(self, doc):
        raise NotImplementedError()

    #####################################
    # Methods which could be replaced by a child class
    def runDailyStats(curTime):
        pass

    def urlMaker(self, escId):
        pass

    def availabilityMaker(self, escId):
        pass

    def getStatusesCollection(self):
        return self.db.escalator_statuses

    def getTwitterApi(self):
        if not self.LIVE:
            self.twitterApi = None
            return None

        if not self.twitterKeys.isSet():
            self.LIVE = False
            self.twitterApi = None
            return None

        if self.twitterApi is None:
            self.twitterApi = twitterUtils.getApi(self.twitterKeys)
        return self.twitterApi

    ######################################

    def checkWMATAKey(self):
        checkWMATAKey()

    def tick(self):
        curTime = utcnow()
        self.initDB(self.db, curTime)

        # Get current incidents
        inc = self.getIncidents()

        # Run the tick
        self.runTick(self.db, curTime, inc, log = self.log)

    # Execute the tick
    def runTick(self, db, curTime, escIncidents, log = sys.stdout):

        printLog = log.write

        # Get the app state to determine the tick delta
        appStateCol = self.getAppStateCollection()
        appState = appStateCol.find_one()
        lastRunTime = None
        if appState is not None and 'lastRunTime' in appState:
            lastRunTime = appState['lastRunTime'].replace(tzinfo=tzutc)
        tickDelta = (curTime - lastRunTime).total_seconds() \
                    if lastRunTime is not None else 0.0

        # Determine escalators which changed status
        changedStatusDict = self.processIncidents(escIncidents, curTime, tickDelta, log=log)

        log.write('%i escalators have changed status\n'%len(changedStatusDict))

        # Generate tweets for escalators which have changed status
        tweetMsgs = self.generateTweets(changedStatusDict,
                                   availabilityMaker=self.availabilityMaker, 
                                   urlMaker = self.urlMaker
                                   )

        # Store tweets in the escalator_tweet_outbox collection
        self.storeTweets(tweetMsgs)

        # Generate the daily stats message if necessary.
        self.runDailyStats(curTime)

        # Send tweets. Only tweet live if the metro is open
        tweetLive = self.LIVE and metroIsOpen(curTime)
        if len(tweetMsgs) > MAX_TICK_TWEETS:
            printLog("Disabling live tweeting due to excessive number" +\
                       " of tweets: %i tweets\n"%len(tweetMsgs))
            tweetLive = False
        if tickDelta > SILENCE_GAP:
            printLog("Disabling live tweeting due to tick delta of %i seconds\n"%(int(tickDelta)))
            tweetLive = False

        self.sendTweets(tweetLive=tweetLive)

        # Update the app state
        update = {'$set':  {'lastRunTime' : curTime} }
        self.getAppStateCollection().update({'_id' : 1}, update, upsert = True)

    #####################################
    # Store outgoing tweets in the tweet outbox
    def storeTweets(self, tweetMsgs):
        if not tweetMsgs:
            return
        curTime = utcnow()
        docs = [{'msg' : m, 'sent' : False, 'time': curTime} for m in tweetMsgs]
        self.getTweetOutbox().insert(docs)

    ##########################################################
    # Send tweets which have been stored in the twitter outbox
    # Only tweet if tweetLive is True
    def sendTweets(self, tweetLive=False):

        twitterApi = self.getTwitterApi()
        tweetOutbox = self.getTweetOutbox()
        log = self.log

        # Purge the outbox of any stale tweets which have not been sent in last hour
        curTime = utcnow()
        staleTime = curTime - timedelta(hours=1)
        log.write('Before removing stale tweets, outbox size %i\n'%tweetOutbox.count())
        tweetOutbox.remove({'time' : {'$lt' : staleTime}})
        log.write('After removing stale tweets, outbox size %i\n'%tweetOutbox.count())

        toSend = list(tweetOutbox.find({'sent' : False}))
        if tweetLive:
            log.write('Tweets are live.\n')
        else:
            log.write('Tweets are not live.\n')
        for doc in toSend:
            msg = doc['msg']
            log.write('Tweet Msg: %s\n'%msg)
            try:
                if tweetLive:
                    twitterApi.PostUpdate(msg)
                # Mark the tweet as sent
                tweetOutbox.update({'_id' : doc['_id']}, {'$set' : {'sent' : True}})
            except TwitterError as e:
                log.write('Caught TwitterError: %s\n'%str(e))

        # Remove all sent tweets from the outbox
        tweetOutbox.remove({'sent' : True})

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
    ########################################################
    def processIncidents(self, curIncidents, curTime, tickDelta, log=sys.stdout):

        if isNaive(curTime):
            raise RuntimeError('curTime cannot be naive datetime')

        db = self.db
        dbg = self.dbg

        log = log.write
        log('processIncidents: Processing %i incidents\n'%len(curIncidents))

        # Add any escalators or symptom codes if we are seeing them for the first time
        for inc in curIncidents:
            dbUtils.updateDBFromIncidentData(db, inc, curTime)

        # Update our local copy of common database structures
        dbg.update()

        # Create dictionary of escalator to the current status
        escIdToCurStatus = defaultdict(lambda: OP_CODE)
        incStatus = lambda inc: (dbg.unitToEscId[inc.UnitId], dbg.symptomToId[inc.SymptomDescription])
        escIdToCurStatus.update(incStatus(inc) for inc in curIncidents)

        # Get the last known statuses for all escalators.
        # Recast escStatuses as a defaultdict
        escStatusItems = self.getLatestStatuses().items()

        default_entry = {'lastFix' : None,
                         'lastBreak' : None,
                         'lastInspection' : None,
                         'lastOp' : None,
                         'lastStatus' : None}
        escStatuses = defaultdict(lambda: default_entry)
        escStatuses.update(escStatusItems)

        #####################
        # DEBUG: FIND MISSING ENTRIES
#        missing = (escId for escId, escStatus in escStatuses.iteritems() if escStatus['lastStatus'] is None)
#        missing = list(missing)
#        log("DEBUG: Have %i units that are missing last status!\n"%len(missing))
#        log("\n".join(missing) + "\n")

        escIdToLastStatus = defaultdict(lambda: OP_CODE)
        escIdToLastStatus.update((escId, escStatus['lastStatus']['symptom_code']) for
                                  escId, escStatus in escStatuses.iteritems())

        # Determine those escalators that have changed status
        escIds = sorted(set(escIdToCurStatus.keys() + escIdToLastStatus.keys()))
        oldStatuses = (escIdToLastStatus[escId] for escId in escIds)
        newStatuses = (escIdToCurStatus[escId] for escId in escIds)
        changedStatus = [(escId, oldStatus, newStatus)
                         for escId,oldStatus,newStatus in zip(escIds, oldStatuses, newStatuses)
                         if oldStatus != newStatus]

        # Update the database with escalators that have changed status 
        changedStatusDict = {}
        statusCollection = self.getStatusesCollection()
        for escId, oldStatus, newStatus in changedStatus:

            doc = {'escalator_id' : escId,
                   'time' : curTime,
                   'tickDelta' : tickDelta,
                   'symptom_code' : int(newStatus)}

            # Add the new status to the database
            statusCollection.insert(doc)
            
            # Add entry to the changedStatusDict
            statusDict = escStatuses[escId]
            statusDict['newStatus'] = doc
            changedStatusDict[escId] = statusDict

            # Trigger any additional changes due to this updated status
            self.statusUpdateCallback(doc)


        return changedStatusDict

    #######################################
    # Generate tweet msgs using the changedStatusDict
    # Return a list of tweets
    def generateTweets(self, changedStatusDict, availabilityMaker=None, urlMaker=None):

        db = self.db
        dbg = self.dbg

        if not changedStatusDict:
            return []

        operational_code = dbg.symptomToId['OPERATIONAL']
        docToStr = lambda d: doc2Str(d, dbg.escIdToUnit, dbg.symptomCodeToSymptom)

        # Extend a tweet by appending another string only if it doesnt violate
        # tweet legnth
        def extendTweet(msg1, msg2):
            if not msg2:
                return msg1
            newmsg = '%s %s'%(msg1, msg2)
            return newmsg if len(newmsg) <= TWEET_LEN else msg1

        def extendTweetUrl(msg1, url):
            newL = len(msg1) + 23 # 22 for url, plus space
            newmsg = '%s %s'%(msg1, url)
            return newmsg if newL <= TWEET_LEN else msg1

        def getSymptomCodeCategory(code):
            symptom = dbg.symptomCodeToSymptom[code]
            return symptomToCategory[symptom]

        tweetMsgs = []
        for escId, statusDict in changedStatusDict.iteritems():

            curStatus = statusDict['newStatus']
            lastStatus = statusDict['lastStatus']
            curSymptomCategory = getSymptomCodeCategory(curStatus['symptom_code'])
            lastSymptomCategory = getSymptomCodeCategory(lastStatus['symptom_code'])
            curSymptom = dbg.symptomCodeToSymptom[curStatus['symptom_code']]
            lastSymptom = dbg.symptomCodeToSymptom[lastStatus['symptom_code']]
           
            # Get 6 char escalator code
            unit = dbg.escIdToUnit[escId][0:6]
            escData = dbg.escIdToEscData[escId]
            stationCode = escData['station_code']
            station = stations.codeToShortName[stationCode]

            tweetMsg = ''

            if lastSymptomCategory == 'ON':

                # This unit has broken, or turned off
                pfx = 'Off' if curSymptomCategory != 'BROKEN' else 'Broken'
                tweetMsg = '{pfx}! #{station} #{unit}. Status is {symptom}.'
                tweetMsg = tweetMsg.format(pfx=pfx,
                                           station=station,
                                           unit=unit,
                                           symptom=curSymptom)

                if curSymptomCategory == 'BROKEN':
                    # Add to tweet "Last broke X days ago."
                    lastFix = statusDict['lastFix']
                    timeSinceLastFix = (curStatus['time'] - lastFix['time']).total_seconds() if lastFix else None
                    lastBrokeStr = makeLastBrokeTimeStr(timeSinceLastFix)
                    tweetMsg = extendTweet(tweetMsg, lastBrokeStr)

            elif curSymptomCategory == 'ON':

                # This unit is back online. It either represents a transition from a broken state,
                # turned off state, or inspection state.

                # This unit has broken, or turned off
                pfx = 'Fixed' if lastSymptomCategory == 'BROKEN' else 'On'
                tweetMsg = '{pfx}! #{station} #{unit}. Status was {symptom}.'
                tweetMsg = tweetMsg.format(pfx=pfx,
                                           station=station,
                                           unit=unit,
                                           symptom=lastSymptom)

                # Get the downtime
                lastOpEndTime = statusDict['lastOp'].get('end_time', None)
                downTime = (curStatus['time'] - lastOpEndTime).total_seconds() if lastOpEndTime else None
                if downTime:
                    downTimeStr = secondsToTimeStrCompact(downTime)
                    tweetMsg = extendTweet(tweetMsg, 'Downtime %s'%downTimeStr)
            else:
                # This represents a transition between non-operational states. Tweet
                # about the updated state change
                tweetMsg = 'Updated: #{station} #{unit}. Status now {symptom2}, was {symptom1}.'
                tweetMsg = tweetMsg.format(station=station, unit=unit,
                                           symptom1 = lastSymptom  ,
                                           symptom2 = curSymptom)

            # Tack on availability data
            if availabilityMaker:
                availabilityStr = availabilityMaker(escId)
                if availabilityStr:
                    tweetMsg = extendTweet(tweetMsg, availabilityStr)

            # Tack on url string
            if urlMaker:
                urlStr = urlMaker(escId)
                if urlStr:
                    tweetMsg = extendTweetUrl(tweetMsg, urlStr)

            tweetMsgs.append(tweetMsg)

        return tweetMsgs

####################################################
# Convert seconds to a time string
# example: 160 minutes = "2 hrs, 40 min."
def secondsToTimeStr(sec):
    timeStr = ''
    if sec > 60:
        days = int(sec / (60*60*24))
        rem = int(sec - (60*60*24)*days)
        hr = int(rem / (60*60))
        rem = int(rem - hr*(60*60))
        mn = int(rem/60)
        timeStr = []
        if days > 0:
            sfx = 'days' if days > 1 else 'day'
            timeStr.append('%i %s'%(days, sfx))
        if hr > 0:
            sfx = 'hrs' if hr > 1 else 'hr'
            timeStr.append('%i %s'%(hr,sfx))
        if mn > 0:
            timeStr.append('%i min'%mn)
        timeStr = ', '.join(timeStr)
    return timeStr

####################################################
# Convert seconds to a string of the form HH:mm
def secondsToTimeStrCompact(sec):
    timeStr = ''
    hrs = int(sec/3600.0)
    rem = sec - hrs*3600
    minutes = int(rem/60.0)
    rem = rem - 60*minutes
    timeStr = '{hr:0>2d}h{min:0>2d}m'.format(hr=hrs,min=minutes)
    return timeStr


def makeLastBrokeTimeStr(secs):
    if secs is None:
        return ''
    if secs <= 0:
        return ''
    secPerDay = 3600*24.0
    lastBrokeDays = int(secs/secPerDay)
    if lastBrokeDays == 0:
        lastBrokeStr = 'Last broke earlier today.'
    elif lastBrokeDays == 1:
        lastBrokeStr = 'Last broke yesterday.'
    elif lastBrokeDays > 1:
        lastBrokeStr = 'Last broke %i days ago.'%lastBrokeDays
    return lastBrokeStr
