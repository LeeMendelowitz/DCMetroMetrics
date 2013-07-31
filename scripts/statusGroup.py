# statusGroup.py from descriptors import setOnce, computeOnce
from metroTimes import TimeRange, isNaive
from collections import defaultdict, Counter
from descriptors import setOnce, computeOnce
from copy import deepcopy
import sys
import dbUtils
import metroTimes

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
    startTime = setOnce('startTime')
    endTime = setOnce('endTime')

    def __init__(self, statuses, startTime = None, endTime = None):
        """
        statuses:  A list of statuses. To properly count the number of break statuses,
                   and inspection statuses, the statuses should include the statuses
                   that preceed and follow in order to provide context.
                   Statuses should be sorted in ascending order. 
        startTime: The start of the time range of interest (as a non-naive datetime).
                   If None, the time of the first status is used.
        endTime:   The end of the time range of interest (as a non-naive datetime).
                   If None, the time of the last status is used.
        """

        _checkAllTimesNotNaive(statuses)

        timesProvided = (startTime or endTime)

        self.allStatuses = statuses

        if not statuses:
            self.statuses = []
            return

        # The statuses must be sorted in ascending order, and
        # all statuses (except the last) must have end_time defined.
        lastTime = None
        numStatuses = len(statuses)
        for i, s in enumerate(statuses):
            if lastTime and s['time'] < lastTime:
                raise RuntimeError('StatusGroup: statuses are not sorted in ascending order')
            lastTime = s['time']

        for i,s in enumerate(statuses):
            if i < (numStatuses - 1) and 'end_time' not in s:
                raise RuntimeError('Status must have end_time defined')

        startTime = startTime or statuses[0]['time']
        endTime = endTime or statuses[-1].get('end_time', None) or statuses[-1]['time']

        # If the last status is missing end_time, then it is still current. Mark
        # it as active so we know that the status is still ongoing.
        if 'end_time' not in statuses[-1]:
            lastStatus = deepcopy(statuses[-1])
            lastStatus['isActive'] = True
            statuses[-1] = lastStatus
        
        # Adjust the startTime or endTime bounds if they are too loose
        if startTime < statuses[0]['time']:
            startTime = statuses[0]['time']
        if 'end_time' in statuses[-1] and endTime > statuses[-1]['end_time']:
            endTime = statuses[-1]['end_time']

        self.startTime = startTime
        self.endTime = endTime

        if (self.endTime < self.startTime):
            raise RuntimeError('Start time must be less than end time')

        # Trim the status list to the specified startTime and endTime
        duringTimePeriod = None
        if timesProvided:
            beforeTimePeriod = [s for s in self.allStatuses if s['time'] < startTime]
            duringTimePeriod = [s for s in self.allStatuses if
                                (s['time'] >= startTime) and (s['time'] <= endTime)]
            afterTimePeriod = [s for s in self.allStatuses if s['time'] > endTime]
            assert(len(beforeTimePeriod) + len(duringTimePeriod) + len(afterTimePeriod) == len(self.allStatuses))

            # The last status which starts before the time period may overlap the
            # time period, in which case it should be included.
            if beforeTimePeriod:
                lastStatusBefore = beforeTimePeriod[-1]
                if (not duringTimePeriod) or (duringTimePeriod[0]['time'] > startTime):
                    duringTimePeriod = [lastStatusBefore] + duringTimePeriod
            
            # Trim the starting time of the first status and the ending time of the last
            # status to the time period
            #
            # Take care only to change a copy of the status,
            # and not the status itself.
            firstStatus = duringTimePeriod[0] if duringTimePeriod else None
            if firstStatus and  startTime > firstStatus['time']:
                firstStatus = deepcopy(firstStatus) 
                firstStatus['time'] = startTime
                duringTimePeriod = [firstStatus] + duringTimePeriod[1:]
        else:
            duringTimePeriod = self.allStatuses

        lastStatus = duringTimePeriod[-1] if duringTimePeriod else None
        if lastStatus:
            # Take care only to change a copy of the status,
            # and not the status itself.
            lastStatus = deepcopy(lastStatus)
            lastStatus['end_time'] = endTime
            duringTimePeriod = duringTimePeriod[:-1] + [lastStatus]

        _checkStatusListSane(duringTimePeriod)
        self.statuses = duringTimePeriod

    @computeOnce
    def statusTimeRanges(self):
        return [TimeRange(s['time'], s['end_time']) for s in self.statuses]

    @computeOnce
    def timeRange(self):
        return TimeRange(self.startTime, self.endTime)

    @computeOnce
    def absTime(self):
        return self.timeRange.absTime

    @computeOnce
    def metroOpenTime(self):
        return self.timeRange.metroOpenTime

    @computeOnce
    def symptomCategoryCounts(self):
        return Counter(s['symptomCategory'] for s in self.statuses)

    @computeOnce
    def symptomCounts(self):
        return Counter(s['symptom'] for s in self.statuses)

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
        startTime = self.startTime
        endTime = self.endTime
        for s in self.allStatuses:
            if s['symptomCategory'] == 'ON':
                wasBroken = False
            elif s['symptomCategory'] == 'BROKEN':
                if not wasBroken and s['time'] >= startTime and s['time'] <= endTime:
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
        startTime = self.startTime
        endTime = self.endTime
        for s in self.allStatuses:
            if s['symptomCategory'] == 'BROKEN':
                wasBroken = True
            elif s['symptomCategory'] == 'ON':
                if wasBroken and s['time'] >= startTime and s['time'] <= endTime:
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
        startTime = self.startTime
        endTime = self.endTime
        for s in self.statuses:
            if s['symptomCategory'] == 'INSPECTION':
                if not wasInspection and s['time'] >= startTime and s['time'] <= endTime:
                    yield s
                wasInspection = True
            elif s['symptomCategory'] == 'ON':
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

    ######################################
    # Get the amount of metro open time allocated to each symptom
    @computeOnce
    def symptomTimeAllocation(self):
        scts = dbUtils.symptomCodeToSymptom
        return dict((scts[code], time) for code,time in self.symptomCodeTimeAllocation.iteritems())

    ######################################
    # Get the amount of absolute time allocated to each symptom 
    @computeOnce
    def symptomAbsTimeAllocation(self):
        scts = dbUtils.symptomCodeToSymptom
        return dict((scts[code], time) for code,time in self.symptomCodeAbsTimeAllocation.iteritems())

    @computeOnce
    def symptomCodeToTimeRanges(self):
        sympCodeToTimeRanges = defaultdict(list)
        symptomCodes = [s['symptom_code'] for s in self.statuses]
        for sc, tr in zip(symptomCodes, self.statusTimeRanges):
            sympCodeToTimeRanges[sc].append(tr)
        return sympCodeToTimeRanges

    @computeOnce
    def symptomCategoryToTimeRanges(self):
        sympCatToTimeRanges = defaultdict(list)
        symptomCategories = [s['symptomCategory'] for s in self.statuses]
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
        p(s['unit_id'] + ' - ' + s['station_name'])
        tfmt = "%m/%d/%y %I:%M %p"
        for s in self.statuses:
            try:
                totalSeconds = (s['end_time'] - s['time']).total_seconds()
            except KeyError:
                totalSeconds = 0.0
            msg = '\t'.join([
                            s['time'].strftime(tfmt),
                            s['symptom'], 
                            metroTimes.secondsToHMS(totalSeconds)
                            ])
            p(msg)

    


#############################################################  
def _checkAllTimesNotNaive(statusList):
    for s in statusList:
        if isNaive(s['time']):
            raise RuntimeError('Times cannot be naive')
        if 'end_time' in s and isNaive(s['end_time']):
            raise RuntimeError('Times cannot be naive')

#############################################################            
# Check that each status has a 'time' and 'end_time' defined
# and that the list is sorted            
def _checkStatusListSane(statusList):
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

def yieldNothing():
    return 
    yield


#######################################################################
# Class to summarize a list of consecutive statuses for a single escalator.
class StatusGroup(StatusGroupBase):

    def __init__(self, statuses, startTime = None, endTime = None):
        StatusGroupBase.__init__(self, statuses, startTime, endTime)

    ##############################
    # Return outages which start in the specified time period
    @computeOnce
    def outageStatuses(self):
        return [o for o in self._genOutageStatuses()]

    def _genOutageStatuses(self):
        outageStatuses = []
        startTime = self.startTime
        for s in self.statuses:
            if s['symptomCategory'] == 'ON':
                if outageStatuses:
                    outage = Outage(outageStatuses)
                    if outage.startTime >= startTime:
                        yield outage
                    outageStatuses = []
            else:
                outageStatuses.append(s)
        if outageStatuses:
            outage = Outage(outageStatuses)
            if outage.startTime >= startTime:
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
        statuses:  A list of statuses. To properly count the number of break statuses,
                   and inspection statuses, the statuses should include the statuses
                   that preceed and follow in order to provide context.
                   Statuses should be sorted in ascending order. 
        startTime: The start of the time range of interest (as a non-naive datetime).
                   If None, the time of the first status is used.
        endTime:   The end of the time range of interest (as a non-naive datetime).
                   If None, the time of the last status is used.
        """

        if isinstance(statuses, dict):
            statuses = [statuses]

        if any(s['symptomCategory']=='ON' for s in statuses):
            raise RuntimeError('Outage should not have an OPERATIONAL status')

        StatusGroupBase.__init__(self, statuses, startTime=None, endTime=None)

    ##########################
    @computeOnce
    # Return True if the outage is still active. An outage is still active
    # if the last status of the outage is still active, meaning it has not yet
    # been followed by an 'ON' status.
    def is_active(self):
        return self.statuses[-1].get('isActive', False)

    ###################################################################
    # Return the broken statuses in this outage.
    @computeOnce
    def breakStatuses(self):
        return list(self._genBreakStatuses())

    def _genBreakStatuses(self):
        return (b for b in self.allStatuses if b['symptomCategory']=='BROKEN')

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
        return (s for s in self.statuses if s['symptomCategory']=='INSPECTION')

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
        return set(s['symptomCategory'] for s in self.allStatuses)
