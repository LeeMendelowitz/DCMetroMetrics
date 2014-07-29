"""
This module provides functionality to summarize an ordered listing of consecutive statuses
for a single escalator/elevator.

StatusGroupBase: Base class

StatusGroup: Class used to summarize an ordered listing of consecutive statuses for a single
             escalator or elevator.

Outage: Class used to summaraize an ordered listing of consecutive non-operational statuses
        for a single escalator or elevator.
"""
from collections import defaultdict, Counter
from copy import deepcopy
import sys

from ..common.descriptors import setOnce, computeOnce
from ..common import metroTimes
from ..common.metroTimes import TimeRange, isNaive
from .misc_utils import *

###############################################################################
# StatusGroupBase: Summarizes a list of consecutive statuses for a single escalator.
# This base class is used by StatusGroup and Outage classes
class StatusGroupBase(object):

    """
    Helper class to summarize a time series of statuses for a single escalator.
    """

    # These attributes can be set once, and are read-only thereafter
    statuses = setOnce('statuses') # This will hold statuses constrained to the specified time period
    allStatuses = setOnce('allStatuses') # This will hold the statuses passed to __init__
    start_time = setOnce('start_time')
    end_time = setOnce('end_time')

    def __init__(self, statuses, start_time = None, end_time = None):
        """
        statuses:  A list of statuses. To properly count the number of break statuses,
                   and inspection statuses, the statuses should include the statuses
                   that preceed and follow in order to provide context.
                   Statuses should be sorted in ascending order. 
        start_time: The start of the time range of interest (as a non-naive datetime).
                   If None, the time of the first status is used.
        end_time:   The end of the time range of interest (as a non-naive datetime).
                   If None, the time of the last status is used.
        """

        checkAllTimesNotNaive(statuses)

        timesProvided = (start_time or end_time)

        self.allStatuses = statuses

        if not statuses:
            self.statuses = []
            return

        # The statuses must be sorted in ascending order, and
        # all statuses (except the last) must have end_time defined.
        lastTime = None
        numStatuses = len(statuses)
        for i, s in enumerate(statuses):
            if lastTime and s.time < lastTime:
                raise RuntimeError('StatusGroup: statuses are not sorted in ascending order')
            lastTime = s.time

        for i,s in enumerate(statuses):
            s_end_time = getattr(s, 'end_time', None)
            if i < (numStatuses - 1) and not s_end_time:
                raise RuntimeError('Status must have end_time defined')

        start_time = start_time or statuses[0].time
        end_time = end_time or getattr(statuses[-1], 'end_time', None) or getattr(statuses[-1], 'time')

        # If the last status is missing end_time, then it is still current. Mark
        # it as active so we know that the status is still ongoing.
        if 'end_time' not in statuses[-1]:
            lastStatus = deepcopy(statuses[-1])
            lastStatus.is_active = True
            statuses[-1] = lastStatus
        
        # Adjust the start_time or end_time bounds if they are too loose
        if start_time < statuses[0].time:
            start_time = statuses[0].time

        last_status_end_time = getattr(statuses[-1], 'end_time', None)
        if last_status_end_time and end_time > last_status_end_time:
            end_time = last_status_end_time

        self.start_time = start_time
        self.end_time = end_time

        if (self.end_time < self.start_time):
            raise RuntimeError('Start time must be less than end time')

        # Trim the status list to the specified start_time and end_time
        duringTimePeriod = None
        if timesProvided:
            beforeTimePeriod = [s for s in self.allStatuses if s.time < start_time]
            duringTimePeriod = [s for s in self.allStatuses if
                                (s.time >= start_time) and (s.time <= end_time)]
            afterTimePeriod = [s for s in self.allStatuses if s.time > end_time]
            assert(len(beforeTimePeriod) + len(duringTimePeriod) + len(afterTimePeriod) == len(self.allStatuses))

            # The last status which starts before the time period may overlap the
            # time period, in which case it should be included.
            if beforeTimePeriod:
                lastStatusBefore = beforeTimePeriod[-1]
                if (not duringTimePeriod) or (duringTimePeriod[0].time > start_time):
                    duringTimePeriod = [lastStatusBefore] + duringTimePeriod
            
            # Trim the starting time of the first status and the ending time of the last
            # status to the time period
            #
            # Take care only to change a copy of the status,
            # and not the status itself.
            firstStatus = duringTimePeriod[0] if duringTimePeriod else None
            if firstStatus and  start_time > firstStatus.time:
                firstStatus = deepcopy(firstStatus) 
                firstStatus.time = start_time
                duringTimePeriod = [firstStatus] + duringTimePeriod[1:]
        else:
            duringTimePeriod = self.allStatuses

        lastStatus = duringTimePeriod[-1] if duringTimePeriod else None
        if lastStatus:
            # Take care only to change a copy of the status,
            # and not the status itself.
            lastStatus = deepcopy(lastStatus)
            lastStatus['end_time'] = end_time
            duringTimePeriod = duringTimePeriod[:-1] + [lastStatus]

        _checkStatusListSane(duringTimePeriod)
        self.statuses = duringTimePeriod

    @computeOnce
    def statusTimeRanges(self):
        return [TimeRange(s.time, s.end_time) for s in self.statuses]

    @computeOnce
    def timeRange(self):
        return TimeRange(self.start_time, self.end_time)

    @computeOnce
    def absTime(self):
        return self.timeRange.absTime

    @computeOnce
    def metroOpenTime(self):
        return self.timeRange.metroOpenTime

    @computeOnce
    def symptomCategoryCounts(self):
        return Counter(s.symptom_category for s in self.statuses)

    @computeOnce
    def symptomCounts(self):
        return Counter(s.symptom for s in self.statuses)

    ###################################################################
    # Count the number of transitions to a broken state within
    # this group of statuses. If the first status is broken, it does
    # not count as a break.
    # Only count at most one break between operational states
    @computeOnce
    def breakStatuses(self):
        return [b for b in self._genBreakStatuses()]

    def _genBreakStatuses(self):
        wasBroken = False
        start_time = self.start_time
        end_time = self.end_time
        for s in self.allStatuses:
            if s.symptom_category == 'ON':
                wasBroken = False
            elif s.symptom_category == 'BROKEN':
                if not wasBroken and s.time >= start_time and s.time <= end_time:
                    yield s
                wasBroken = True

    ######################################################################
    # Count the number of resolved broken states.
    # Transitions such as : CALLBACK/REPAIR -> MINOR REPAIR -> OPERATIONAL only
    # should count as a single fix.
    # this group of statuses
    @computeOnce
    def fixStatuses(self):
        return [f for f in self._genFixStatuses()]

    def _genFixStatuses(self):
        wasBroken = False
        start_time = self.start_time
        end_time = self.end_time
        for s in self.allStatuses:
            if s.symptom_category == 'BROKEN':
                wasBroken = True
            elif s.symptom_category == 'ON':
                if wasBroken and s.time >= start_time and s.time <= end_time:
                    yield s
                wasBroken = False

    ############################
    # Count the number of inspection statuses
    # Only get the first inspection state between operational states
    @computeOnce
    def inspectionStatuses(self):
        return [s for s in self._genInspectionStatuses()]

    def _genInspectionStatuses(self):
        wasInspection = False
        start_time = self.start_time
        end_time = self.end_time
        for s in self.statuses:
            if s.symptom_category == 'INSPECTION':
                if not wasInspection and s.time >= start_time and s.time <= end_time:
                    yield s
                wasInspection = True
            elif s.symptom_category == 'ON':
                wasInspection = False


    ######################################
    # Get the amount of metro open time allocated to each symptom category
    @computeOnce
    def timeAllocation(self):
        symptomCategoryToTime = defaultdict(lambda: 0.0)
        for symptomCategory, trList in self.symptomCategoryToTimeRanges.iteritems():
            symptomCategoryToTime[symptomCategory] = sum(tr.metroOpenTime for tr in trList)
        totalTime = sum(symptomCategoryToTime.values())
        assert(abs(totalTime - self.timeRange.metroOpenTime) < 1E-3)
        return symptomCategoryToTime

    ######################################
    # Get the amount of absolute time allocated to each symptom category
    @computeOnce
    def absTimeAllocation(self):
        symptomCategoryToTime = defaultdict(lambda: 0.0)
        for symptomCategory, trList in self.symptomCategoryToTimeRanges.iteritems():
            symptomCategoryToTime[symptomCategory] = sum(tr.absTime for tr in trList)
        totalTime = sum(symptomCategoryToTime.values())
        assert(abs(totalTime - self.timeRange.absTime < 1E-3))
        return symptomCategoryToTime

    ######################################
    # Get the amount of metro open time allocated to each symptom code
    @computeOnce
    def symptomCodeTimeAllocation(self):
        symptomCodeToTime = defaultdict(lambda: 0.0)
        for symptomCode, trList in self.symptomCodeToTimeRanges.iteritems():
            symptomCodeToTime[symptomCode] = sum(tr.metroOpenTime for tr in trList)
        totalTime = sum(symptomCodeToTime.values())
        assert(abs(totalTime - self.timeRange.metroOpenTime) < 1E-3)
        return symptomCodeToTime

    ######################################
    # Get the amount of absolute time allocated to each symptom code
    @computeOnce
    def symptomCodeAbsTimeAllocation(self):
        symptomCodeToTime = defaultdict(lambda: 0.0)
        for symptomCode, trList in self.symptomCodeToTimeRanges.iteritems():
            symptomCodeToTime[symptomCode] = sum(tr.absTime for tr in trList)
        totalTime = sum(symptomCodeToTime.values())
        assert(abs(totalTime - self.timeRange.absTime) < 1E-3)
        return symptomCodeToTime

#    ######################################
#    # Get the amount of metro open time allocated to each symptom
#    @computeOnce
#    def symptomTimeAllocation(self):
#        scts = dbUtils.symptomCodeToSymptom
#        return dict((scts[code], time) for code,time in self.symptomCodeTimeAllocation.iteritems())
#
#    ######################################
#    # Get the amount of absolute time allocated to each symptom 
#    @computeOnce
#    def symptomAbsTimeAllocation(self):
#        scts = dbUtils.symptomCodeToSymptom
#        return dict((scts[code], time) for code,time in self.symptomCodeAbsTimeAllocation.iteritems())

    @computeOnce
    def symptomCodeToTimeRanges(self):
        sympCodeToTimeRanges = defaultdict(list)
        symptomCodes = [s.symptom_category for s in self.statuses]
        for sc, tr in zip(symptomCodes, self.statusTimeRanges):
            sympCodeToTimeRanges[sc].append(tr)
        return sympCodeToTimeRanges

    @computeOnce
    def symptomCategoryToTimeRanges(self):
        sympCatToTimeRanges = defaultdict(list)
        symptomCategories = [s.symptom_category for s in self.statuses]
        for sc, tr in zip(symptomCategories, self.statusTimeRanges):
            sympCatToTimeRanges[sc].append(tr)
        return sympCatToTimeRanges

    @computeOnce
    def brokenTimePercentage(self):
        brokenTime = self.timeAllocation['BROKEN']
        brokenTimePercentage = 0.0
        if self.metroOpenTime > 0.0:
            brokenTimePercentage = float(brokenTime)/self.metroOpenTime
        return brokenTimePercentage

    def printStatuses(self, handle = sys.stdout):
        p = lambda m: handle.write(str(m) + '\n')
        s = self.statuses[0]
        p(s.unit_id + ' - ' + s.station_name)
        tfmt = "%m/%d/%y %I:%M %p"
        for s in self.statuses:
            try:
                totalSeconds = (s.end_time - s.time).total_seconds()
            except KeyError:
                totalSeconds = 0.0
            msg = '\t'.join([
                            s.time.strftime(tfmt),
                            s.symptom_description, 
                            metroTimes.secondsToHMS(totalSeconds)
                            ])
            p(msg)

    





#######################################################################
# Class to summarize a list of consecutive statuses for a single escalator.
class StatusGroup(StatusGroupBase):

    def __init__(self, statuses, start_time = None, end_time = None):
        StatusGroupBase.__init__(self, statuses, start_time, end_time)

    ##############################
    # Return outages which start in the specified time period
    @computeOnce
    def outageStatuses(self):
        return [o for o in self._genOutageStatuses()]

    def _genOutageStatuses(self):
        outageStatuses = []
        start_time = self.start_time
        for s in self.statuses:
            if s.symptom_category == 'ON':
                if outageStatuses:
                    outage = Outage(outageStatuses)
                    if outage.start_time >= start_time:
                        yield outage
                    outageStatuses = []
            else:
                outageStatuses.append(s)
        if outageStatuses:
            outage = Outage(outageStatuses)
            if outage.start_time >= start_time:
                yield outage

###############################################################################
# Outage
# Used to represent an escalator outage (a list of consecutive non-operational statuses)
class Outage(StatusGroupBase):

    """
    Helper class to summarize an outage escalator outage
    """

    def __init__(self, statuses):
        """
        statuses:  A list of consecutive non-operational statuses.
                   Statuses should be sorted in ascending order. 
        start_time: The start of the time range of interest (as a non-naive datetime).
                   If None, the time of the first status is used.
        end_time:   The end of the time range of interest (as a non-naive datetime).
                   If None, the time of the last status is used.
        """

        if isinstance(statuses, dict):
            statuses = [statuses]

        if any(s.symptom_category == 'ON' for s in statuses):
            raise RuntimeError('Outage should not have an OPERATIONAL status')

        StatusGroupBase.__init__(self, statuses, start_time=None, end_time=None)

    ##########################
    @computeOnce
    # Return True if the outage is still active. An outage is still active
    # if the last status of the outage is still active, meaning it has not yet
    # been followed by an 'ON' status.
    def is_active(self):
        return getattr(self.statuses[-1], 'is_active', False)

    ###################################################################
    # Return the broken statuses in this outage.
    @computeOnce
    def breakStatuses(self):
        return list(self._genBreakStatuses())

    def _genBreakStatuses(self):
        return (b for b in self.allStatuses if b.symptom_category=='BROKEN')

    ######################################################################
    # Count the number of resolved broken states.
    # Transitions such as : CALLBACK/REPAIR -> MINOR REPAIR -> OPERATIONAL only
    # should count as a single fix.
    # this group of statuses
    @computeOnce
    def fixStatuses(self):
        return []

    def _genFixStatuses(self):
        return yieldNothing()
        
    ############################
    # Count the number of inspection statuses
    # Only get the first inspection state between operational states
    @computeOnce
    def inspectionStatuses(self):
        return list(self._genInspectionStatuses())

    def _genInspectionStatuses(self):
        return (s for s in self.statuses if s.symptom_category == 'INSPECTION')

    #############################
    @computeOnce
    def is_break(self):
        return True if self.breakStatuses else False

    @computeOnce
    def is_inspection(self):
        return True if self.inspectionStatuses else False

    @computeOnce
    def is_off(self):
        return 'OFF' in self.categories

    @computeOnce
    def is_rehab(self):
        return 'REHAB' in self.categories

    @computeOnce
    def categories(self):
        return set(s.symptom_category for s in self.allStatuses)

#############################################################            
            
def _checkStatusListSane(statusList):
    """Check that each status has a 'time' and 'end_time' defined
    and that the list is sorted
    """
    lastTime = None
    for s in statusList:
        if 'end_time' not in s:
            raise RuntimeError('Status missing end_time')
        if 'time' not in s:
            raise RuntimeError('Status missing time')
        if s['time'] > s['end_time']:
            raise RuntimeError('Status has bad starting/ending time')
        if lastTime and s['time'] < lastTime:
            raise RuntimeError('Status not sorted properly')
        lastTime = s['time']