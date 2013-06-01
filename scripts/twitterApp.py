import os
import sys
import cPickle
import makeEscalatorRequest
metroApiRequest = makeEscalatorRequest.twitterRequest()
from utils import *
import tweeter
from time import sleep
import stations
from incident import Incident
from datetime import datetime, date, time, timedelta
from tweepy.error import TweepError
import dbUtils
import utils

import argparse

TWEETLEN = 140

# If the twitter app has not run in the last 1.5 hours,
# silence tweeting. This is to avoid a flurry of tweets all
# at once.
SILENCE_AFTER_GAP = 1.5*3600

# Number of escalators in the system
NUM_ESCALATORS = 588

OUTPUT_DIR = os.environ.get('OPENSHIFT_DATA_DIR', None)
if OUTPUT_DIR is None:
    OUTPUT_DIR = os.getcwd()

parser = argparse.ArgumentParser(description='Run @MetroEscalators app')
parser.add_argument('--test', action='store_true', help='Run in Test Mode (does not tweet)')

def updateDB(incidents, curTime, tickDelta):
    db = dbUtils.getDB()

    # Initialize the escalator database if necessary
    numEscalators = db.escalators.count()
    NUM_ESCALATORS = 588
    if numEscalators < NUM_ESCALATORS:
        escalatorTsv = os.path.join(os.environ['OPENSHIFT_DATA_DIR'], 'escalators.tsv')
        escData = utils.readEscalatorTsv(escalatorTsv)
        assert(len(escData) == NUM_ESCALATORS)
        dbUtils.initializeEscalators(db, escData, curTime)

    res = dbUtils.processIncidents(db, incidents, curTime, tickDelta) 
    return res

#############################################
# Defines the state of the twitter app.
class State(object):
    
    def __init__(self, pickle_file_old, pickle_file_new):
        self.pickle_file_old = pickle_file_old
        self.pickle_file_new = pickle_file_new
        self.setAttributes()

    # Add required attributes which may be missing in older versions of the state object
    def setAttributes(self):

        # Set the next inspection report time to be 8 AM of the next day
        nextInspectionReportTime = datetime.combine(date=date.today(), time=time(hour=8))
        if datetime.now() > nextInspectionReportTime:
            nextInspectionReportTime += timedelta(days=1)

        attrList = [ ('unitIdToBrokeTime', {}),
                     ('unitIdToLastFixTime', {}),
                     ('inspectedUnits', set()),
                     ('numBreaks', 0),
                     ('numFixes', 0),
                     ('availabilities', []),
                     ('nextInspectionReportTime', nextInspectionReportTime)]

        # Set attributes to their default values
        for attr, val in attrList:
            if not hasAttr(self, attr):
                setattr(self, attr, val)


    def write(self, handle = sys.stdout):

        opened = False
        if isinstance(handle, str):
            opened = True
            fname = handle
            handle = open(fname, 'w')

        cPickle.dump(self, handle)

        if opened:
            handle.close()

    @staticmethod
    def readStateFile(fname):
        fin = open(fname)
        state = cPickle.load(fin)
        fin.close()
        state.setAttributes()
        return state

#############################################
# Initiate the app by creating two pickle files of incidents
def init(stateFile):
    pickleFile1 = TwitterApp.request()
    sleep(2)
    pickleFile2 = TwitterApp.request()
    state = State(pickleFile1, pickleFile2)

    stateFileOut = open(stateFile, 'w')
    state.write(stateFileOut)
    stateFileOut.close()


#############################################
class TwitterApp(object):
    
    def __init__(self, stateFile, LIVE=True, QUIET=False):
        self.LIVE = LIVE
        self.QUIET = QUIET
        self.stateFile = stateFile
        self.state = State.readStateFile(stateFile)
        self.numIncidents = 0
        self.availability = 1.0
        self.tweeter = None

    ##########################################
    # Get the list of current incidents from the metroAPI.
    # Store in the
    # collection of current incidents. Update the 
    # app state collection.
    def getIncidents(self):
        res = metroApiRequest()
        curTime = datetime.now()
        incidents = res['incidents']
        incidents = [i for i in incidents if i.isEscalator()]

        # Store the current list of incidents


        self.updateAppState(runTime = curTime)
        

    def updateAppState(self, runTime = None, nextReportTime = None):
        assert(self.mongo_db)
        updateSpec = [('runTime', runTime), ('nextReportTime', nextReportTime)]
        updateSpec = [(k,v) for k,v in updateSpec if v is not None]
        if updateSpec:
            updateSpec = dict(updateSpec)
            self.mongo_db.appstate.update({'_id' : 1}, {'$set' : updateSpec})

    def getTweeter(self):
        if self.tweeter is None:
            DEBUG = not self.LIVE
            self.tweeter = tweeter.Tweeter(DEBUG=DEBUG)
        return self.tweeter

    # Perform one run
    def tick(self):

        #self.tweetPulse()

        # Read the pickle file created during the last run
        oldPickleFile = self.state.pickle_file_new
        oldRes = cPickle.load(open(oldPickleFile))
        lastTime = oldRes['requestTime']
        oldIncidents = oldRes['incidents']
        oldEscalators, oldElevators = splitIncidentsByUnitType(oldIncidents)

        # Generate a new pickle file for this run
        newPickleFile = self.request()
        newRes = cPickle.load(open(newPickleFile))
        thisTime = newRes['requestTime']
        newIncidents = newRes['incidents']

        newEscalators, newElevators = splitIncidentsByUnitType(newIncidents)

        # Compute the escalator availability this tick
        self.numIncidents = len(newEscalators)
        self.availability = 1.0 - self.numIncidents/float(NUM_ESCALATORS)

        if metroIsOpen(thisTime):
            self.state.availabilities.append(self.availability)


        numOld = len(oldEscalators)
        numNew = len(newEscalators)
        sys.stdout.write('Read %i incidents\n'%len(newIncidents))
        sys.stdout.write('Read %i old escalator incidents, %i new escalator incidents\n'%(numOld, numNew))
        sys.stdout.flush()

        # Temporarily disable tweeting if the difference between consecutive updates is too long
        disabled = False
        tickDelta = (thisTime - lastTime).total_seconds()
        if tickDelta > 60*2.0:
            sys.stdout.write('DELAY WARNING! The twitter app has not run in %.2f seconds!\n'%tickDelta)
        if self.LIVE and tickDelta > SILENCE_AFTER_GAP:
            disabled = True
            self.LIVE = False
        
        # Tweet this report
        self.reportDifferences(oldEscalators, newEscalators, thisTime)
        self.processInspections(newEscalators)

        # Renable tweeting
        if disabled:
            self.LIVE = True

        # Update the state
        self.state.pickle_file_old = oldPickleFile
        self.state.pickle_file_new = newPickleFile
        self.state.write(self.stateFile)

        updateDB(newEscalators, thisTime, tickDelta)

    # Make tweets and update the state's unitIdToBrokeTime
    def reportDifferences(self, oldList, newList, curTime):

        # Perform escalator diff
        diffRes = diffIncidentLists(oldList, newList)

        # For new incidents, distinguish between broken and turned off.
        broken = []
        turnedOff = []
        for inc in diffRes['newIncidents']:
            if inc.notBroken():
                turnedOff.append(inc)
            else:
                broken.append(inc)

        # Make availability string.
        availabilityStr = '%5.1f%% work.'%(100*self.availability)

        # Tweet units that are broken
        for inc in broken:
            self.state.numBreaks += 1
            station = stations.codeToShortName[inc.StationCode] 
            unit = inc.UnitName
            status = inc.SymptomDescription
            self.state.unitIdToBrokeTime[inc.UnitId] = curTime
            lastBrokeTime = self.state.unitIdToLastFixTime.get(inc.UnitId, None)

            lastBrokeStr = ''
            if lastBrokeTime is not None:
                secPerDay = 3600*24.0
                lastBrokeDays = int((curTime - lastBrokeTime).total_seconds()/secPerDay)
                if lastBrokeDays == 0:
                    lastBrokeStr = 'Last broke earlier today'
                elif lastBrokeDays == 1:
                    lastBrokeStr = 'Last broke yesterday'
                elif lastBrokeDays > 1:
                    lastBrokeStr = 'Last broke %i days ago'%lastBrokeDays

            msg = 'BROKEN! #{station}. Unit #{unit}. Status {status}'.format(unit=unit, station=station, status=status)

            # Append last broke string if there is space
            msg2 = '%s. %s'%(msg, lastBrokeStr)
            if len(msg2) <= TWEETLEN:
                msg = msg2
            msg2 = '%s. %s'%(msg, availabilityStr)
            if len(msg2) <= TWEETLEN:
                msg = msg2

            self.tweet(msg)

        # Tweet units that are turned off
        for inc in turnedOff:
            station = stations.codeToShortName[inc.StationCode] 
            unit = inc.UnitName
            status = inc.SymptomDescription
            msg = 'OFF! #{station}. Unit #{unit}. Status {status}'.format(unit=unit, station=station, status=status)
            #self.tweet(msg) # Don't tweet if unit was turned off
            self.state.unitIdToBrokeTime[inc.UnitId] = curTime

        # Tweet units that are fixed
        for inc in diffRes['resolvedIncidents']:
            station = stations.codeToShortName[inc.StationCode] 
            unit = inc.UnitName
            status = inc.SymptomDescription

            # Distinguish between units that were broken vs. units that aren't
            wasBroken = inc.isBroken()
            lastBrokeTime = None
            if wasBroken:
                self.state.numFixes += 1
                self.state.unitIdToLastFixTime[inc.UnitId] = curTime

            secondsOutOfService = 0
            if inc.UnitId in self.state.unitIdToBrokeTime:
                secondsOutOfService = int((curTime - self.state.unitIdToBrokeTime[inc.UnitId]).total_seconds())
                del self.state.unitIdToBrokeTime[inc.UnitId]
            timeStr = secondsToTimeStrCompact(secondsOutOfService)
            timeStr = 'Downtime %s'%(timeStr)

            msgTitle = 'FIXED' if wasBroken else 'ON'
            msg = '{title}! #{station}. Unit #{unit}. Status was {status}. {downtime}'.format(title=msgTitle, unit=unit, station=station, status=status, downtime=timeStr)

            # Add availabilty string
            msg2 = '%s. %s'%(msg, availabilityStr)
            if len(msg2) <= TWEETLEN:
                msg = msg2

            # Only tweet if the unit was broken and is now fixed.
            if wasBroken:
                self.tweet(msg)

        # Tweet units that have changed status
        for inc1, inc2 in diffRes['changedIncidents']:
            assert(inc1.UnitId == inc2.UnitId)
            station = stations.codeToShortName[inc1.StationCode] 
            unit = inc1.UnitName
            status1 = inc1.SymptomDescription
            status2 = inc2.SymptomDescription
            msg = 'UPDATED: #{station}. Unit #{unit}. Was {status1}, now {status2}'.format(unit=unit, station=station, status1=status1, status2=status2)
            # Only tweet if one of the states is a broken state:
            if inc1.isBroken() or inc2.isBroken():
                self.tweet(msg)

            # Transition to broken
            if (not inc1.isBroken() and inc2.isBroken()):
                self.state.numBreaks += 1
            elif (not inc2.isBroken() and inc1.isBroken()):
                self.state.unitIdToLastFixTime[inc1.UnitId] = curTime
                self.state.numFixes += 1

        # Clean up any units which are not in the latest incident list but are in the unitIdToBrokeTime dict
        currentBrokenUnits = set(i.UnitId for i in newList)
        entriesToRemove = [k for k in self.state.unitIdToBrokeTime.keys() if k not in currentBrokenUnits]
        for k in entriesToRemove:
            del self.state.unitIdToBrokeTime[k]

    def processInspections(self, newIncidents):
        unitIds = (inc.UnitId for inc in newIncidents if inc.isInspection())
        self.state.inspectedUnits.update(unitIds)
        timeToReport = datetime.now() > self.state.nextInspectionReportTime

        if timeToReport:

            numInspections = len(self.state.inspectedUnits)

            def makeEscalatorStr(num):
                myS = '%i esc.'%num if num != 1 else '1 esc.'
                return myS

            def computeAvailability():
                a = self.state.availabilities
                return 100*float(sum(a))/len(a) if a else 100.0

            inspectionStr = makeEscalatorStr(numInspections)
            fixStr = str(self.state.numFixes) + (' have been fixed' if self.state.numFixes !=1 else ' has been fixed')
            breakStr = str(self.state.numBreaks) + (' have broken' if self.state.numBreaks !=1 else ' has broken')

            avgAvail = computeAvailability()

            msg = 'Good Morning DC! #WMATA Escalator #DailyStats Inspected={0}, Broken={1}, Fixed={2}, Availability={3:5.1f}%'
            msg = msg.format(numInspections, self.state.numBreaks, self.state.numFixes, avgAvail)
            self.tweet(msg)

            self.state.inspectedUnits = set()
            self.state.numBreaks = 0
            self.state.numFixes = 0
            self.state.availabilities = []

            # Set the next inspection report time to be 8 AM of the next day
            tomorrow = date.today() + timedelta(days=1)
            self.state.nextInspectionReportTime = datetime.combine(date=tomorrow, time=time(hour=8))
        

    # Make a request from Metro API and store the result in a pickle file
    @staticmethod
    def request():
        timeStrFormat = '%Y_%m_%d_%H_%M_%S'
        res = makeEscalatorRequest.twitterRequest()
        resTime = res['requestTime'].strftime(timeStrFormat)
        pickleName = '%s.pickle'%resTime
        pickleName = os.path.join(OUTPUT_DIR, pickleName)
        fout = open(pickleName, 'w')
        cPickle.dump(res, fout)
        fout.close()
        return pickleName

    def tweetPulse(self):
        timeStrFormat = '%Y_%m_%d_%H_%M_%S'
        timeStr = datetime.now().strftime(timeStrFormat)
        self.tweet('Running now.... time: %s'%timeStr)

    def tweet(self, msg):
        curTime = datetime.now() # Store this instead of getting it each time?
        metroOpen = metroIsOpen(curTime)
        if not self.QUIET:
            sys.stdout.write('MetroOpen: %s\n'%str(metroOpen))
            sys.stdout.write('LIVE: %s\n'%str(self.LIVE))
            sys.stdout.write('Tweeting: %s\n'%msg)
        if self.LIVE and metroOpen:
            try:
                self.getTweeter().tweet(msg)
            except TweepError as e:
                sys.stdout.write('CAUGHT EXCEPTION! Reason: %s Message: %s\n'%(e.reason, e.message))
        

def main():

    args = parser.parse_args()
    LIVE = True if not args.test else False

    stateFile = os.path.join(OUTPUT_DIR, 'twitterApp.state')

    if not os.path.exists(stateFile):
        init(stateFile)

    # Read the state file
    app = TwitterApp(stateFile, LIVE=LIVE)
    app.tick()

# Return true if Metro is open at the given time
def metroIsOpen(dt):
    curTime = time(hour=dt.hour, minute=dt.minute, second = dt.second)
    curDay = dt.weekday()
    if curDay in (0, 1, 2, 3, 4):
        # Monday thru Thursday, Friday
        openTime = time(hour=5)
        isOpen = (curTime >= openTime) 
    elif curDay in (5,6):
        # Saturday, Sunday
        amCloseTime = time(hour=3)
        amOpenTime = time(hour=7)
        isOpen = (curTime <= amCloseTime) or (curTime >= amOpenTime)
    else:
        raise RuntimeError('Code should not get here!')
    return isOpen


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




