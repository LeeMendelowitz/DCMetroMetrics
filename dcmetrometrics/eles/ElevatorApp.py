"""
eles.elevator

Define the ElevatorApp class, which is reponsible for
querying the WMATA API for elevator outages, storing them
in a database, and generating tweets for the @MetroElevator
twitter app.
"""

# python modules
import os
import sys
from time import sleep
from datetime import datetime, date, time, timedelta

# TEST CODE
if __name__ == '__main__':
    import dcmetrometrics.test.setup

# Custom modules
from ..common import dbGlobals, twitterUtils, utils, stations
from ..common.metroTimes import utcnow, tzutc, metroIsOpen, toLocalTime
from . import dbUtils
from .dbUtils import invDict
from ..third_party.twitter import TwitterError
from ..keys import MetroElevatorKeys
from .Incident import Incident
from .defs import symptomToCategory, OPERATIONAL_CODE as OP_CODE, NUM_ELEVATORS
from .ELESApp import ELESApp, getELESIncidents

#############################################
# Get elevator incidents
def getElevatorIncidents(log=sys.stdout):
    eleIncidents = getELESIncidents()['incidents'] # This will throw an exception
                                                   # if the request fails
    eleIncidents = [i for i in eleIncidents if i.isElevator()]
    return eleIncidents

#############################################
class ElevatorApp(ELESApp):
    
    def __init__(self, log, LIVE=True, QUIET=False):
        ELESApp.__init__(self, log, LIVE, QUIET)

    def initDB(self, db, curTime):

        # Add the operational code
        db.symptom_codes.update({'_id' : OP_CODE},
                                {'$set' : {'symptom_desc' : 'OPERATIONAL'}},
                                upsert=True)

        # Initialize the escalator/elevator database if necessary
        elevators = self.dbg.getElevatorIds()
        numElevators = len(elevators)

        if numElevators < NUM_ELEVATORS:
            elevatorTsv = os.path.join(os.environ['OPENSHIFT_DATA_DIR'], 'elevators.tsv')
            escData = utils.readEscalatorTsv(elevatorTsv)
            for d in escData:
                d['unit_type'] = 'ELEVATOR'
            dbUtils.initializeEscalators(db, escData, curTime)

        self.dbg.update()

    def getIncidents(self):
        return getElevatorIncidents(log=self.log)

    def getLatestStatuses(self):
        return dbUtils.getLatestStatuses(elevators=True, dbg=self.dbg)

    def getAppStateCollection(self):
        return self.db.elevator_appstate

    def getStatusesCollection(self):
        return self.db.escalator_statuses

    # Trigger webpage regeneration when an elevator changes status
    def statusUpdateCallback(self, doc):
        db = self.db
        eleId = doc['escalator_id']

        # Mark webpages for regeneration
        update = {'$set' : {'forceUpdate':True}}
        eleData = self.dbg.escIdToEscData[eleId]
        stationCode = eleData['station_code']
        stationShortName = stations.codeToShortName[stationCode]

        db.webpages.update({'class' : 'elevator', 'elevator_id' : eleId}, update)
        db.webpages.update({'class' : 'elevatorDirectory'}, update)
        db.webpages.update({'class' : 'stationDirectory'}, update)
        db.webpages.update({'class' : 'station', 'station_name' : stationShortName}, update)

    def getTwitterKeys(self):
        return MetroElevatorKeys

    def getTweetOutbox(self):
        return self.db.elevator_tweet_outbox

    def runDailyStats(self, curTime):
        pass

    # Return a str with escalator availability information.
    @staticmethod
    def availabilityMaker(escId):
        return ''

    # Return a str with the url for the escalator.
    @staticmethod
    def urlMaker(escId):
        return ''

# TEST CODE
if __name__ == "__main__":
    import time
    import sys
    app = ElevatorApp(log=sys.stdout, LIVE=False)
    while True:
        msg = '*'*50 + '\nTEST TICK:\n'
        sys.stdout.write(msg)
        app.tick()
        time.sleep(10)
