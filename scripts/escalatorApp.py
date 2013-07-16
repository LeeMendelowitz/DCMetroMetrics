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
from dbUtils import invDict, getDB, getUnitToId, getSymptomToId
import utils
import twitterUtils
from escalatorRequest import getELESIncidents, WMATA_API_ERROR
from utils import *
from keys import MetroEscalatorKeys
from escalatorDefs import symptomToCategory, OPERATIONAL_CODE
import metroEscalatorsWeb

TWEET_LEN = 140

# Silence tweeting if the tick delay is greater than 20 minutes
SILENCE_GAP = 60*20

# Maximum number of tweets allowed in a single tick. Otherwise
# the tick is silenced
MAX_TICK_TWEETS = 10

# Number of escalators in the system
NUM_ESCALATORS = 588

OUTPUT_DIR = os.environ.get('OPENSHIFT_DATA_DIR', None)
if OUTPUT_DIR is None:
    OUTPUT_DIR = os.getcwd()

def initDB(db, curTime):

    # Add the operational code
    db.symptom_codes.find_and_modify({'_id' : OPERATIONAL_CODE},
                                     update = {'_id' : OPERATIONAL_CODE,
                                               'symptom_desc' : 'OPERATIONAL'},
                                     upsert=True)

    # Initialize the escalator database if necessary
    numEscalators = db.escalators.count()
    if numEscalators < NUM_ESCALATORS:
        escalatorTsv = os.path.join(os.environ['OPENSHIFT_DATA_DIR'], 'escalators.tsv')
        escData = utils.readEscalatorTsv(escalatorTsv)
        assert(len(escData) == NUM_ESCALATORS)
        dbUtils.initializeEscalators(db, escData, curTime)

#############################################
# Get escalator incidents
def getEscalatorIncidents(log=sys.stdout):
    escIncidents = getELESIncidents()['incidents'] # This will throw an exception
                                                   # if the request fails
    escIncidents = [i for i in escIncidents if i.isEscalator()]
    return escIncidents


#############################################
class EscalatorApp(object):
    
    def __init__(self, log, LIVE=True, QUIET=False):
        self.LIVE = LIVE
        self.QUIET = QUIET
        self.numIncidents = 0
        self.availability = 1.0
        self.twitterApi = None
        self.log = log

    def getTwitterApi(self):
        if not self.LIVE:
            self.twitterApi = None
            return None
        if self.twitterApi is None:
            self.twitterApi = twitterUtils.getApi(keys=MetroEscalatorKeys)
        return self.twitterApi

    def tick(self):

        curTime = utcnow()
        db = dbUtils.getDB()
        initDB(db, curTime)

        # Get current incidents
        escIncidents = getEscalatorIncidents(log=self.log)

        # Run the tick
        self.runTick(db, curTime, escIncidents, log = self.log)

    # Execute the tick
    def runTick(self, db, curTime, escIncidents, log = sys.stdout):

        printLog = log.write

        # Get the app state to determine the tick delta
        appState = db.escalator_appstate.find_one()
        lastRunTime = None
        if appState is not None and 'lastRunTime' in appState:
            lastRunTime = appState['lastRunTime'].replace(tzinfo=tzutc)
        tickDelta = (curTime - lastRunTime).total_seconds() \
                    if lastRunTime is not None else 0.0

        # Determine escalators which changed status
        changedStatusDict = dbUtils.processIncidents(db, escIncidents, curTime, tickDelta, log=log)

        # Generate tweets for escalators which have changed status
        tweetMsgs = generateTweets(db, changedStatusDict)

        # Store tweets in the escalator_tweet_outbox collection
        storeTweets(db, tweetMsgs)

        # Generate the daily stats message if necessary.
        self.runDailyStats(db, curTime)

        # Send tweets. Only tweet live if the metro is open
        twitterApi = self.getTwitterApi()
        tweetLive = self.LIVE and metroIsOpen(curTime)
        if len(tweetMsgs) > MAX_TICK_TWEETS:
            printLog("Disabling live tweeting due to excessive number" +\
                       " of tweets: %i tweets\n"%len(tweetMsgs))
            tweetLive = False
        if tickDelta > SILENCE_GAP:
            printLog("Disabling live tweeting due to tick delta of %i seconds\n"%(int(tickDelta)))
            tweetLive = False

        sendTweets(db, twitterApi, tweetLive=tweetLive, log=self.log)

        # Update the app state
        update = {'$set':  {'lastRunTime' : curTime} }
        db.escalator_appstate.update({'_id' : 1}, update, upsert = True)

    def runDailyStats(self, db, curTime):
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
            storeTweets(db, [dailyStatsMsg])

        update = {'$set' : {'lastDailyStatsTime' : curTime}}
        db.escalator_appstate.update({'_id' : 1}, update, upsert = True)


#######################################
# Compute the daily stats for the last 24 hour
def dailyStats(curTime, startTime = None):
    
    escIdToSummary = {}
    # Generate a summary for each escalator
    if startTime is None:
        startTime = curTime - timedelta(hours=24.0)
    endTime = curTime

    escIds = dbUtils.unitToEscId.values()
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
               
#####################################
# Store outgoing tweets in the tweet outbox
def storeTweets(db, tweetMsgs):
    if not tweetMsgs:
        return
    curTime = utcnow()
    docs = [{'msg' : m, 'sent' : False, 'time': curTime} for m in tweetMsgs]
    db.escalator_tweet_outbox.insert(docs)

##########################################################
# Send tweets which have been stored in the twitter outbox
# Only tweet if tweetLive is True
def sendTweets(db, twitterApi, tweetLive=False, log = sys.stdout):

    # Purge the outbox of any stale tweets which have not been sent in last hour
    curTime = utcnow()
    staleTime = curTime - timedelta(hours=1)
    log.write('Before removing stale tweets, outbox size %i\n'%db.escalator_tweet_outbox.count())
    db.escalator_tweet_outbox.remove({'time' : {'$lt' : staleTime}})
    log.write('After removing stale tweets, outbox size %i\n'%db.escalator_tweet_outbox.count())

    toSend = list(db.escalator_tweet_outbox.find({'sent' : False}))
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
            db.escalator_tweet_outbox.update({'_id' : doc['_id']}, {'$set' : {'sent' : True}})
        except TwitterError as e:
            log.write('Caught TwitterError: %s\n'%str(e))

    # Remove all sent tweets from the outbox
    db.escalator_tweet_outbox.remove({'sent' : True})

def main():

    LIVE = False 
    log = sys.stdout
    app = EscalatorApp(log, LIVE=LIVE)
    app.tick()

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
    timeStr = '{hr:0>2d}:{min:0>2d}'.format(hr=hrs,min=minutes)
    return timeStr

if __name__ == '__main__':
    main()


#######################################
# Generate tweet msgs using the changedStatusDict
# Return a list of tweets
def generateTweets(db, changedStatusDict):

    if not changedStatusDict:
        return []

    unitToId = getUnitToId(db)
    escIdToUnit = invDict(unitToId)
    symptomToId = getSymptomToId(db)
    operational_code = symptomToId['OPERATIONAL']
    symptomCodeToSymptom = invDict(symptomToId)
    docToStr = lambda d: doc2Str(d, escIdToUnit, symptomCodeToSymptom)

    availabilityData = dbUtils.getSystemAvailability()


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
        symptom = symptomCodeToSymptom[code]
        return symptomToCategory[symptom]

    tweetMsgs = []
    for escid, statusDict in changedStatusDict.iteritems():

        curStatus = statusDict['newStatus']
        lastStatus = statusDict['lastStatus']
        curSymptomCategory = getSymptomCodeCategory(curStatus['symptom_code'])
        lastSymptomCategory = getSymptomCodeCategory(lastStatus['symptom_code'])
        curSymptom = symptomCodeToSymptom[curStatus['symptom_code']]
        lastSymptom = symptomCodeToSymptom[lastStatus['symptom_code']]
       
        # Get 6 char escalator code
        unit = escIdToUnit[escid][0:6]
        escData = dbUtils.getEsc(db, escid)
        stationCode = escData['station_code']
        station = stations.codeToShortName[stationCode]
        escUrl = metroEscalatorsWeb.escUnitIdToAbsWebPath(unit)

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
                tweetMsg = extendTweet(tweetMsg, 'Downtime %s.'%downTimeStr)
        else:
            # This represents a transition between non-operational states. Tweet
            # about the updated state change
            tweetMsg = 'Updated: #{station} #{unit}. Status now {symptom2}, was {symptom1}.'
            tweetMsg = tweetMsg.format(station=station, unit=unit,
                                       symptom1 = lastSymptom  ,
                                       symptom2 = curSymptom)

        # Tack on availability data
        sAvail = availabilityData['stationToAvailability'][stationCode]
        aStr =  'A=%.1f%%'%(100.0*availabilityData['availability'])
        #wAStr = 'wA=%.1f%%'%(100.0*availabilityData['weightedAvailability'])
        sAstr = 'sA=%.1f%%'%(100.0*sAvail)
        tweetMsg = extendTweet(tweetMsg, aStr)
        tweetMsg = extendTweet(tweetMsg, '%s'%(sAstr))
        tweetMsg = extendTweetUrl(tweetMsg, escUrl)
        tweetMsgs.append(tweetMsg)
    return tweetMsgs

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
