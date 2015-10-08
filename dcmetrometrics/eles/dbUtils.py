"""
eles.dbUtils

Utilities for pulling or writing escalator/elevator data
to the MongoDB collections.
"""

# python imports
import pymongo
from mongoengine import DoesNotExist
import sys
import os
from collections import defaultdict, Counter
from datetime import datetime, time, date, timedelta
from operator import itemgetter, attrgetter
import copy
import gevent
import itertools

# custom imports

from ..common.dbGlobals import G
from ..common import dbGlobals, stations
from ..common.metroTimes import TimeRange, utcnow, isNaive, toUtc, tzutc
from .defs import symptomToCategory, OPERATIONAL_CODE as OP_CODE
from .StatusGroup import StatusGroup
from .models import Unit, UnitStatus, KeyStatuses, SymptomCode
from .misc_utils import *

invert_dict = lambda d: dict((v,k) for k,v in d.iteritems())

def get_one(cursor):
    """
    Get one item from the iterable.
    Return None if there is None.
    """
    try:
        return next(cursor)
    except StopIteration:
        return None

def get_some(cursor, N):
    """
    Get at most N items from the cursor, and return as a list
    """
    return [i for i in itertools.slice(cursor, N)]

def get_first_status_since(statusList, time):
    """
    Get the first status in the status list that starts after time.
    """
    statusList = sorted(statusList, key = itemgetter('time')) # in time ascending
    myRecs = (rec for rec in statusList if rec.time > time)
    return get_one(myRecs)

###############################################################
# Update the database from incident data
# This will add any new escalators or symptom codes that
# have not yet been seen to the appropriate collection
def update_db_from_incident(inc, curTime):
    """
    Add a unit and a symptom to the database from an
    ELES Incident.
    """
    # Add the escalator to the database
    doc = { 'unit_id' : inc.UnitId,
          'station_code' : inc.StationCode,
          'station_name' : stations.codeToName.get(inc.StationCode, None), # Use the station name from stations.py
          'esc_desc' : inc.LocationDescription,
          'station_desc' : inc.StationDesc,
          'unit_type' : inc.UnitType
    }

    # Add this symptom (if we are seeing it for the first time)
    SymptomCode.add(inc.SymptomDescription)

    # Add the unit (if we are seeing it for the first time)
    Unit.add(curTime = curTime, **doc)

def set_unit_key_statuses():
    
    """
    Initialize the KeyUnitStatus records for all escalators and elevators
    by examining their status history.
    """

    # Removal all KeyUnitStatus records.
    KeyStatuses.drop_collection()

    for unit in Unit.objects:
        print "Computing key statuses for unit: %s"%(unit.unit_id)
        unit.compute_key_statuses()



######################################################################
def group_statuses_by_station_code(statuses):
    checkAllTimesNotNaive(statuses)
    stationCodeToStatus = defaultdict(list)
    for s in statuses:
        stationCodeToStatus[s.station_code].append(s)
    return stationCodeToStatus

def group_statuses_by_escalator(statuses):
    checkAllTimesNotNaive(statuses)
    escIdToStatus = defaultdict(list)
    for s in statuses:
        escIdToStatus[s.unit.pk].append(s)
    return escIdToStatus

#####################################################################
# Determine the current escalator availabilities of the system
# Also compute the weighted availability and the station availability
# Exactly one of escalators or elevators must be True.
def get_system_availability(escalators=False, elevators=False):

    raise RuntimeError("Deprecated. Must update this method to use the KeyStatuses collection.")

    DBG = G()

    db = DBG.getDB()

    if sum([escalators, elevators]) != 1:
        raise RuntimeError("escalators or elevators must be True, but not both.")

    latestStatuses = get_latest_statuses(escalators=escalators, elevators=elevators)
    N = len(latestStatuses)

    # Compute availability
    def comput_availability(statusList):
        if not statusList:
            return 1.0
        N = len(statusList)
        numAvail = sum(1 for d in statusList if d['symptomCategory'] == 'ON')
        return float(numAvail)/N

    def compute_weighted_availability(statusList):
        avail = [d for d in statusList if d['symptomCategory'] == 'ON']
        unavail = [d for d in statusList if d['symptomCategory'] != 'ON']

        availWeights = []
        for d in avail:
            sd = stations.codeToStationData.get(d['station_code'], None)
            if not sd:
                availWeights.append(0.0)
            availWeigths.append(sd.get('escalatorWeight', 0.0))

        unavailWeights = []
        for d in unavail:
            sd = stations.codeToStationData.get(d['station_code'], None)
            if not sd:
                unavailWeights.append(0.0)
            unavailWeigths.append(sd.get('escalatorWeight', 0.0))

        wA1 = sum(availWeights)
        wA2 = 1.0 - sum(unavailWeights)
        assert(abs(wA1 - wA2) < 1E-6)
        return wA1

    lastStatuses = [d['lastStatus'] for d in latestStatuses.itervalues()]
    lastStatuses = [s for s in lastStatuses if s is not None]
    numOp = sum(1 for d in lastStatuses if d['symptomCategory'] == 'ON')

    symptomCategoryToCount = Counter(d['symptomCategory'] for d in lastStatuses)
    symptomToCount = Counter(d['symptom'] for d in lastStatuses)

    # Compute overall availability
    availability = comput_availability(lastStatuses)
    weightedAvailability = comput_weighted_availability(lastStatuses) if escalators else 0.0

    # Compute availability for each station
    # Note: Some stations have multiple codes (Gallery Pl, L'Enfant, MetroCenter, FortTotten)
    # GP is 'F01' and 'B01' , L'Enfant is 'F03' and 'D03', FT is 'B06' and 'E06', MC is 'A01', 'C01'
    # stationCodeToAvailability: compute availability for each unique station code
    # stationToAvailability: compute availability for each station. Two codes which refer to
    #                        same station should return same value.
    stationCodeToStatuses = group_statuses_by_station_code(lastStatuses)
    stationGroups = stations.nameToCodes.values()
    stationToStatuses = {}
    for codeGroup in stationGroups:
        allStatuses = [s for c in codeGroup for s in stationCodeToStatuses[c]]
        stationToStatuses.update((c, allStatuses) for c in codeGroup)

    stationCodeToAvailability = dict((k, comput_availability(v)) for k,v in stationCodeToStatuses.iteritems())
    stationToAvailability = dict((k, comput_availability(v)) for k,v in stationToStatuses.iteritems())

    ret = { 'availability' : availability,
            'weightedAvailability' : weightedAvailability,
            'numOp' : numOp,
            'numEsc' : N,
            'symptomCategoryToCount' : symptomCategoryToCount,
            'symptomToCount' : symptomToCount,
            'stationCodeToAvailability' : stationCodeToAvailability,
            'stationToAvailability' : stationToAvailability,
            'stationCodeToStatuses' : stationCodeToStatuses,
            'stationToStatuses' : stationToStatuses,
            'escToLatest' : latestStatuses,
            'lastStatuses' : lastStatuses
          }

    return ret





########################################
# Merge a list of escalator summaries produced by summarize_statuses
# into a single summary. This is useful for compiling
# a summary for a single station
def merge_escalator_summaries(escalatorSummaryList):

    # Accumulate a list of symptom to time dictionaries
    def accumD(timeDictList):
        merged = defaultdict(lambda: 0.0)
        for td in timeDictList:
            for k,v in td.iteritems():
                merged[k] += v
        return merged

    # Accumulate a list of numbers
    def accum(values):
        return sum(values)

    keyAccumulators = [ ('numBreaks', accum),
                        ('numFixes', accum),
                        ('numInspections', accum),
                        ('symptomCodeToTime', accumD),
                        ('symptomCodeToAbsTime', accumD),
                        ('symptomCategoryToTime', accumD),
                        ('symptomCategoryToAbsTime', accumD),
                        ('availableTime', accum),
                        ('metroOpenTime', accum),
                        ('absTime', accum) ]
    merged = {}
    for k, af in keyAccumulators:
        val = af(d[k] for d in escalatorSummaryList)
        merged[k] = val
    # Compute the availability on this merged set
    openTime = float(merged['metroOpenTime'])
    availTime = float(merged['availableTime'])
    merged['availability'] = availTime/openTime if openTime > 0.0 else 1.0
    return merged


#################################################



########################################################
# Given a status list for a single escalator, sorted in descending
# time order, compute a summary:
# - numBreaks
# - numInspections
# - time spent in each status code
# - metro open time spent in each status code
# start_time and end_time must be provided to properly compute the times.
def summarize_statuses(statusList, start_time, end_time):

    # Convert start_time and end_time to utcTimeZone, if necessary
    if start_time is not None:
        start_time = toUtc(start_time)
    if end_time is not None:
        end_time = toUtc(end_time)

    if not statusList:
        return {}

    if(start_time > end_time):
       raise RuntimeError('summarize_statuses: bad start_time/end_time')

    # Reverse the sort order so statuses are in asending order
    fullStatusList = statusList[::-1]
    statusGroup = StatusGroup(fullStatusList, start_time=start_time, end_time=end_time)
    statusList = statusGroup.statuses

    if not statusList:
        default_ret = { 'numBreaks' : 0,
                        'numFixes' : 0,
                        'numInspections' : 0,
                        'symptomCodeToTime' : {},
                        'symptomCodeToAbsTime' : {},
                        'symptomCategoryToTime' : {},
                        'symptomCategoryToAbsTime' : {},
                        'availableTime' : 0,
                        'availability' : 1.0,
                        'metroOpenTime' : 0.0,
                        'brokenTimePercentage' : 0.0,
                        'absTime' : 0.0}
        return default_ret

    breakStatuses = statusGroup.breakStatuses
    fixStatuses = statusGroup.fixStatuses
    inspectionStatuses = statusGroup.inspectionStatuses
    
    numBreaks = len(breakStatuses)
    numFixes = len(fixStatuses)
    numInspections = len(inspectionStatuses)

    for s in statusList:
        if any(getattr(s, k, None) is None for k in ('time', 'end_time')):
            raise RuntimeError('summarize_statuses: status is missing time or end_time field')

    # Summarize the time allocation to various symptoms for this time window
    symptomCodeToTime = statusGroup.symptomCodeTimeAllocation
    symptomCodeToAbsTime = statusGroup.symptomCodeAbsTimeAllocation
    symptomCategoryToTime = statusGroup.timeAllocation
    symptomCategoryToAbsTime = statusGroup.absTimeAllocation

    availTime = symptomCategoryToTime['ON']
    timeRange = statusGroup.timeRange
    metroOpenTime = timeRange.metroOpenTime
    absTime = timeRange.absTime
    availability = availTime/metroOpenTime if metroOpenTime > 0.0 else 1.0

    ret = { 'numBreaks' : numBreaks,
            'numFixes' : numFixes,
            'numInspections' : numInspections,
            'symptomCodeToTime' : symptomCodeToTime,
            'symptomCodeToAbsTime' : symptomCodeToAbsTime,
            'symptomCategoryToTime' : symptomCategoryToTime,
            'symptomCategoryToAbsTime' : symptomCategoryToAbsTime,
            'availableTime' : availTime,
            'availability' : availability,
            'brokenTimePercentage' : statusGroup.brokenTimePercentage,
            'metroOpenTime' : metroOpenTime,
            'absTime' : absTime}

    return ret


############################################################################
# Get a summary of all escalators for the specified time period
def get_all_unit_summaries(start_time=None, end_time=None, escalators=False, elevators=False):

    DBG = G()

    # Convert start_time and end_time to utcTimeZone, if necessary
    if start_time is not None:
        start_time = toUtc(start_time)
    if end_time is not None:
        end_time = toUtc(end_time)

    if escalators and not elevators:
        oids = DBG.getEscalatorIds()
    elif elevators and not escalators:
        oids = DBG.getElevatorIds()
    else:
        # Get both escalators and elevators
        oids = Unit.objects.distinct('pk')

    curTime = utcnow()

    unit_to_summary = {}

    # NOTE: This function could be improved by making a single call to db.escalator_statuses.find() and
    # aggregating.
    for oid in oids:
        gevent.sleep(0.0)
        unit = Unit.objects(pk = oid).get()
        statuses = unit.get_statuses(start_time = start_time, end_time = end_time)
        #statuses = get_unit_statuses(object_id = oid, start_time = start_time, end_time = end_time)
        et = end_time if end_time is not None else curTime
        st = start_time if start_time is not None else min(s['time'] for s in statuses)
        summary = summarize_statuses(statuses, st, et)
        summary['statuses'] = statuses
    
        # Add escalator meta-data to the summary
        unit = DBG.escIdToEscData[oid]
        summary['unit'] = unit

        unit_to_summary[oid] = summary

    return unit_to_summary

###############################################################################
# Get all escalator statuses.
# Return a dictionary from escalator to status list, in chronological order
def get_all_unit_statuses():

    statuses = UnitStatus.objects.order_by('time').select_related()
    unit_id_to_statuses = defaultdict(list)

    for s in statuses:
        s.add_timezones()
        unit_id_to_statuses[s.unit.pk].append(s)

    return unit_id_to_statuses
