########################################################
# Module to store global variables computed from the database.
# These global variables store information on escalators, elevators,
# and symptom codes which are unlikely to change during execution.
#
# The global variables should only update if an escalator, elevator
# or symptom code is seen for the first time.
#######################################################
import pymongo
from escalatorDefs import OPERATIONAL_CODE
import os

invDict = lambda d: dict((v,k) for k,v in d.iteritems())

# Global Variables
db = None
unitToEscId = None
escIdToUnit = None
symptomToId = None
symptomCodeToSymptom = None
escIdToEscData = None
opCode = OPERATIONAL_CODE
escList = None
eleList = None
esc_ids = None
ele_ids = None
all_ids = None
escIdToEscData = None # For escalators and elevators

def update():
    """
    Update global variables by querying the database
    """
    global db, unitToEscId, escIdToUnit, symptomToId, symptomCodeToSymptom, escIdToEscData,\
           opCode, esc_ids, ele_ids, all_ids,\
           escIdToEscData, eleIdToEleData

    db = getDB(force=True)

    # Add the operational code
    db.symptom_codes.update({'_id' : OPERATIONAL_CODE},
                                    {'$set' : {'symptom_desc' : 'OPERATIONAL'} },
                                     upsert=True)

    # Build unitToEscId & escIdToUnit
    escList = list(db.escalators.find())
    unitToEscId = dict((d['unit_id'],d['_id']) for d in escList)
    escIdToUnit = invDict(unitToEscId)

    # Build symptomDict, symptomCodeToSymptom
    symptoms = list(db.symptom_codes.find())
    symptomToId = dict((d['symptom_desc'],d['_id']) for d in symptoms)
    opCode = symptomToId['OPERATIONAL']
    symptomCodeToSymptom = invDict(symptomToId)

    # Build escalator/elevator data
    escList = list(db.escalators.find({'unit_type' : 'ESCALATOR'}))
    eleList = list(db.escalators.find({'unit_type' : 'ELEVATOR'}))
    escIdToEscData = dict((d['_id'], d) for d in escList+eleList)
    esc_ids = db.escalators.find({'unit_type' : 'ESCALATOR'}).distinct('_id')
    ele_ids = db.escalators.find({'unit_type' : 'ELEVATOR'}).distinct('_id')
    all_ids = db.escalators.find().distinct('_id')


def getDB(force=False):
    global db
    if (db is not None) and (not force):
        return db

    host = os.environ["OPENSHIFT_MONGODB_DB_HOST"]
    port = int(os.environ["OPENSHIFT_MONGODB_DB_PORT"])
    user = os.environ["OPENSHIFT_MONGODB_DB_USERNAME"]
    password = os.environ["OPENSHIFT_MONGODB_DB_PASSWORD"]
    client = pymongo.MongoClient(host, port)

    # Try authenticating with admin
    db = client.admin
    #serr('Attempting Authentication\n')
    res = db.authenticate(user, password)
    #serr('Authenticate returned: %s\n'%str(res))

    db = client.MetroEscalators
    return db

########################################
# Create dictionary from escalator unit id
# to the pymongo id
def getUnitToId():
    escList = list(db.escalators.find())
    unitToEscId = dict((d['unit_id'],d['_id']) for d in escList)
    return unitToEscId

def getEsc(escId):
    db = getDB()
    return db.escalators.find_one({'_id' : escId})

#########################################
def getEscalatorIds():
    """
    Return ids for units which are escalators
    """
    return esc_ids

def getElevatorIds():
    """
    Return ids for units which are elevators
    """
    return ele_ids

def getUnitIds():
    """
    Return ids for all units (escalators & elevators)
    """
    return all_ids



# Update the global variables
update()
