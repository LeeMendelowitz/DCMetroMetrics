import os
import sys
import cPickle
import makeEscalatorRequest
from utils import *
import tweeter
from time import sleep
import stations
from incident import Incident
from datetime import datetime, date, time, timedelta

import argparse

OUTPUT_DIR = os.environ.get('OPENSHIFT_DATA_DIR', None)
if OUTPUT_DIR is None:
    OUTPUT_DIR = os.getcwd()

parser = argparse.ArgumentParser(description='Run @MetroEscalators app')
parser.add_argument('--test', action='store_true', help='Run in Test Mode (does not tweet)')

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
                     ('inspectedUnits', set()),
                     ('numBreaks', 0),
                     ('numFixes', 0),
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
        self.tweeter = None

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
        oldIncidents = oldRes['incidents']
        oldEscalators, oldElevators = splitIncidentsByUnitType(oldIncidents)

        # Generate a new pickle file for this run
        newPickleFile = self.request()
        newRes = cPickle.load(open(newPickleFile))
        newIncidents = newRes['incidents']
        newEscalators, newElevators = splitIncidentsByUnitType(newIncidents)

        sys.stdout.write('Read %i incidents\n'%len(newIncidents))
        sys.stdout.flush()

        # Tweet this report
        self.reportDifferences(oldEscalators, newEscalators)
        self.processInspections(newEscalators)

        # Update the state
        self.state.pickle_file_old = oldPickleFile
        self.state.pickle_file_new = newPickleFile
        self.state.write(self.stateFile)

    # Make tweets and update the state's unitIdToBrokeTime
    def reportDifferences(self, oldList, newList):

        curTime = datetime.now()

        # Perform escalator diff
        diffRes = diffIncidentLists(oldList, newList)

        # For new incidents, distinguish between broken and turned off.
        offCategories = set( ['TURNED OFF/WALKER', 'PREV. MAINT. INSPECTION'] )
        broken = []
        turnedOff = []
        for inc in diffRes['newIncidents']:
            if inc.SymptomDescription in offCategories:
                turnedOff.append(inc)
            else:
                broken.append(inc)

        # Tweet units that are broken
        for inc in broken:
            self.state.numBreaks += 1
            station = stations.codeToName[inc.StationCode] 
            unit = inc.UnitName
            status = inc.SymptomDescription
            msg = 'BROKEN! {station}. Unit #{unit}. Status {status}'.format(unit=unit, station=station, status=status)
            self.tweet(msg)
            self.state.unitIdToBrokeTime[inc.UnitId] = curTime

        # Tweet units that are turned off
        for inc in turnedOff:
            station = stations.codeToName[inc.StationCode] 
            unit = inc.UnitName
            status = inc.SymptomDescription
            msg = 'OFF! {station}. Unit #{unit}. Status {status}'.format(unit=unit, station=station, status=status)
            self.tweet(msg)
            self.state.unitIdToBrokeTime[inc.UnitId] = curTime

        # Tweet units that are fixed
        for inc in diffRes['resolvedIncidents']:
            station = stations.codeToName[inc.StationCode] 
            unit = inc.UnitName
            status = inc.SymptomDescription

            # Only count this escalator as a fix if it wasn't a Walker or an Inspection
            wasBroken = inc.isBroken()
            if wasBroken:
                self.state.numFixes += 1

            # Compute the downtime
            timeStr = ''
            #secondsOutOfService = int((curTime - inc.TimeOutOfService).total_seconds())
            secondsOutOfService = 0
            if inc.UnitId in self.state.unitIdToBrokeTime:
                secondsOutOfService = int((curTime - self.state.unitIdToBrokeTime[inc.UnitId]).total_seconds())
                del self.state.unitIdToBrokeTime[inc.UnitId]

            if secondsOutOfService > 0:
                days = int(secondsOutOfService / (60*60*24))
                rem = int(secondsOutOfService - (60*60*24)*days)
                hr = int(rem / (60*60))
                rem = int(rem - hr*(60*60))
                mn = int(rem/60)
                timeStr = []
                if days > 0:
                    sfx = 'days' if days > 1 else 'day'
                    timeStr.append('%i %s'%(days, sfx))
                if hr > 0:
                    timeStr.append('%i hrs'%hr)
                if mn > 0:
                    timeStr.append('%i min'%mn)
                timeStr = 'Downtime %s.'%(', '.join(timeStr))

            msgTitle = 'FIXED' if wasBroken else 'ON'
            msg = '{title}! {station}. Unit #{unit}. Status was {status}.'.format(title=msgTitle, unit=unit, station=station, status=status)
            if timeStr:
                msg += ' %s'%timeStr
            self.tweet(msg)

        # Tweet units that have changed status
        for inc1, inc2 in diffRes['changedIncidents']:
            station = stations.codeToName[inc1.StationCode] 
            unit = inc1.UnitName
            status1 = inc1.SymptomDescription
            status2 = inc2.SymptomDescription
            msg = 'UPDATED: {station}. Unit #{unit}. Was {status1}, now {status2}'.format(unit=unit, station=station, status1=status1, status2=status2)
            self.tweet(msg)

            # Transition to broken
            if (not inc1.isBroken() and inc2.isBroken()):
                self.state.numBreaks += 1
            elif (not inc2.isBroken() and inc1.isBroken()):
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
                myS = '%i escalators'%num if num != 1 else '1 escalator'
                return myS

            inspectionStr = makeEscalatorStr(numInspections)
            fixStr = makeEscalatorStr(self.state.numFixes) + (' have been fixed' if self.state.numFixes !=1 else ' has been fixed')
            breakStr = makeEscalatorStr(self.state.numBreaks) + (' have broken' if self.state.numBreaks !=1 else ' has broken')
            msg = 'Good morning DC! In the past 24 hours, @wmata has inspected {0}. {1}, and {2}. #WMATA'
            msg = msg.format(inspectionStr, breakStr, fixStr)
            self.tweet(msg)

            self.state.inspectedUnits = set()
            self.state.numBreaks = 0
            self.state.numFixes = 0

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
        if not self.QUIET:
            sys.stdout.write('Tweeting: %s\n'%msg)
        if self.LIVE:
            self.getTweeter().tweet(msg)
        

def main():

    args = parser.parse_args()
    LIVE = True if not args.test else False

    stateFile = os.path.join(OUTPUT_DIR, 'twitterApp.state')

    if not os.path.exists(stateFile):
        init(stateFile)

    # Read the state file
    app = TwitterApp(stateFile, LIVE=LIVE)
    app.tick()



if __name__ == '__main__':
    main()




