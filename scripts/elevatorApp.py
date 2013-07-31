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
from keys import MetroElevatorKeys
from escalatorDefs import symptomToCategory, OPERATIONAL_CODE
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

    def getIncidents(self):
        return getElevatorIncidents(log=self.log)

    def getLatestStatuses(self):
        return dbUtils.getLatestStatuses(elevators=True)

    def getAppStateCollection(self):
        db = dbUtils.getDB()
        return db.elevator_appstate

    def getStatusesCollection(self):
        db = dbUtils.getDB()
        return db.escalator_statuses

    # Trigger webpage regeneration when an escalator changes status
    def statusUpdateCallback(self, doc):
        pass

    def getTwitterKeys(self):
        return MetroElevatorKeys

    def getTweetOutbox(self):
        db = dbUtils.getDB()
        return db.elevator_tweet_outbox

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
