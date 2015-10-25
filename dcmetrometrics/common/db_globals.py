"""
common.dbGlobals

Module to store global variables computed from the database.
These global variables store information on escalators, elevators,
and symptom codes.

The global variables should only update if an escalator, elevator
or symptom code is seen for the first time.
"""

import pymongo
import os
import mongoengine
from mongoengine import DoesNotExist
from ..eles.defs import OPERATIONAL_CODE as OP_CODE, symptomToCategory


from .globals import MONGODB_HOST, MONGODB_PORT, MONGODB_USERNAME, MONGODB_PASSWORD

invert_dict = lambda d: dict((v,k) for k,v in d.iteritems())

class _DBGlobals(object):

    def __init__(self):
        self.db = None
        self.unitToEscId = None
        self.escIdToUnit = None
        self.symptom_dict = None # Symptom Description to symptom object
        self.OPERATIONAL = None
        self.symptoms = None # Symptom primary key to symptom description
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
        connect()

        self.db = getDB()

        from ..eles.models import Unit, UnitStatus, SymptomCode

        # Save the operational symptom code if it does not already exist.
        try:
            operational = SymptomCode.objects(description="OPERATIONAL").get()
        except DoesNotExist:
            operational = SymptomCode(description = "OPERATIONAL", category = "ON")
            operational.save()

        self.OPERATIONAL = operational

        # Check all other symptom codes, and update the categories that are specified in the definitions file.
        for symptom in SymptomCode.objects:
            symptom.category = symptomToCategory[symptom.description]
            symptom.save()

        # Build unitToEscId & escIdToUnit
        units = list(Unit.objects)

        self.unitToEscId = dict((d.unit_id,d.pk) for d in units)
        self.escIdToUnit = invert_dict(self.unitToEscId)
        self.unitIdToUnit = dict((d.unit_id, d) for d in units)

        # Build symptomDict, symptomCodeToSymptom
        symptoms = list(SymptomCode.objects)
        self.symptom_dict = dict((d.description, d) for d in symptoms)
        self.symptoms = symptoms

        # Build escalator/elevator data
        self.escList = [d for d in units if d.is_escalator()]
        self.eleList = [d for d in units if d.is_elevator()]
        self.escIdToEscData = dict((d.pk, d) for d in units)

        self.esc_ids = [d.pk for d in self.escList]
        self.ele_ids = [d.pk for d in self.eleList]
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
        Get the Mongo Database, using pymongo
        """
        if self.db is None:
            self.db = getDB()
        return self.db

def getDB():
    """
    Return the db via pymongo
    """
    client = pymongo.MongoClient(MONGODB_HOST, MONGODB_PORT)
    
    db = client.MetroEscalators
    if MONGODB_USERNAME and MONGODB_PASSWORD:
        res = db.authenticate(MONGODB_USERNAME, MONGODB_PASSWORD)

    return db

def connect():
    """
    Connect to the database via mongoengine
    """
    from mongoengine import connect
    connect('MetroEscalators', host=MONGODB_HOST, port=MONGODB_PORT, username=MONGODB_USERNAME, password=MONGODB_PASSWORD)

_G = None # Global object
def G():
    """Return a shared global object which maintains the escalator and elevator directory in memory.
    """

    global _G

    if _G:
        return _G
    
    _G = _DBGlobals()
    _G.update()
    return _G


