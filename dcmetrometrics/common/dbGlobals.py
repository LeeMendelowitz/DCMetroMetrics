"""
common.dbGlobals

Module to store global variables computed from the database.
These global variables store information on escalators, elevators,
and symptom codes which are unlikely to change during execution.
#
The global variables should only update if an escalator, elevator
or symptom code is seen for the first time.
"""

import pymongo
import os

from ..eles.defs import OPERATIONAL_CODE as OP_CODE

invDict = lambda d: dict((v,k) for k,v in d.iteritems())

class DBGlobals(object):

    def __init__(self):
        self.db = None
        self.unitToEscId = None
        self.escIdToUnit = None
        self.symptomToId = None
        self.symptomCodeToSymptom = None
        self.escIdToEscData = None
        self.escList = None
        self.eleList = None
        self.esc_ids = None
        self.ele_ids = None
        self.all_ids = None
        self.escIdToEscData = None # For escalators and elevators
        self.update()

    def update(self):
        """
        Update global variables by querying the database
        """

        self.db = getDB()

        # Add the operational code to the database
        self.db.symptom_codes.update({'_id' : OP_CODE},
                                        {'$set' : {'symptom_desc' : 'OPERATIONAL'} },
                                         upsert=True)

        # Build unitToEscId & escIdToUnit
        unitList = list(self.db.escalators.find())
        self.unitToEscId = dict((d['unit_id'],d['_id']) for d in unitList)
        self.escIdToUnit = invDict(self.unitToEscId)

        # Build symptomDict, symptomCodeToSymptom
        symptoms = list(self.db.symptom_codes.find())
        self.symptomToId = dict((d['symptom_desc'],d['_id']) for d in symptoms)
        self.symptomCodeToSymptom = invDict(self.symptomToId)

        # Build escalator/elevator data
        self.escList = [d for d in unitList if d['unit_type']=='ESCALATOR']
        self.eleList = [d for d in unitList if d['unit_type']=='ELEVATOR']
        self.escIdToEscData = dict((d['_id'], d) for d in unitList)
        self.esc_ids = [d['_id'] for d in self.escList]
        self.ele_ids = [d['_id'] for d in self.eleList]
        self.all_ids = self.esc_ids + self.ele_ids

    def getEscalatorIds(self):
        """
        Return ids for units which are escalators
        """
        return self.esc_ids

    def getElevatorIds(self):
        """
        Return ids for units which are elevators
        """
        return self.ele_ids

    def getUnitIds(self):
        """
        Return ids for all units (escalators & elevators)
        """
        return self.all_ids

    def getDB(self):
        """
        Get the Mongo Database
        """
        if self.db is None:
            self.db = getDB()
        return self.db

def getDB():

    host = os.environ["OPENSHIFT_MONGODB_DB_HOST"]
    port = int(os.environ["OPENSHIFT_MONGODB_DB_PORT"])
    user = os.environ["OPENSHIFT_MONGODB_DB_USERNAME"]
    password = os.environ["OPENSHIFT_MONGODB_DB_PASSWORD"]
    client = pymongo.MongoClient(host, port)

    db = client.MetroEscalators
    res = db.authenticate(user, password)

    return db

def connect():
    from mongoengine import connect
    host = os.environ["OPENSHIFT_MONGODB_DB_HOST"]
    port = int(os.environ["OPENSHIFT_MONGODB_DB_PORT"])
    user = os.environ["OPENSHIFT_MONGODB_DB_USERNAME"]
    password = os.environ["OPENSHIFT_MONGODB_DB_PASSWORD"]
    connect('MetroEscalators', host=host, port=port, username=user, password=password)

