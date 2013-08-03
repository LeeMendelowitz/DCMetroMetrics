# python modules
import os
import sys
from time import sleep
from datetime import datetime, date, time, timedelta
from metroTimes import utcnow, tzutc, metroIsOpen, toLocalTime

# TEST CODE
if __name__ == '__main__':
    import test_setup

# Custom modules
import stations
from incident import Incident
from twitter import TwitterError
import dbUtils
from dbUtils import invDict
import utils
import twitterUtils
import dbGlobals
from escalatorRequest import getELESIncidents, WMATA_API_ERROR
from utils import *
from keys import MetroElevatorKeys
from escalatorDefs import symptomToCategory, OPERATIONAL_CODE as OP_CODE, NUM_ELEVATORS
import metroEscalatorsWeb
from ELESApp import ELESApp

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

    # Trigger webpage regeneration when an escalator changes status
    def statusUpdateCallback(self, doc):
        pass

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
