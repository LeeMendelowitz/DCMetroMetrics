"""
eles.incident

class Incident: An item on the WMATA list of escalator outages.
"""


from ..common.utils import *
from ..common import utils
from datetime import date, datetime, time

###################################################################
class Incident(object):
    """
    Repepresent an escalator/elevator outage
    """

    def __init__(self, data):

        keys = [u'SymptomDescription',
         u'LocationDescription',
         u'UnitName',
         u'UnitType',
         u'SymptomCode',
         u'TimeOutOfService',
         u'DateOutOfServ',
         u'StationName',
         u'StationCode',
         u'DateUpdated',
         u'UnitStatus',
         u'DisplayOrder']

        requiredKeys = ['SymptomDescription',
                        'LocationDescription',
                        'UnitName',
                        'UnitType',
                        'SymptomCode',
                        'StationName',
                        'StationCode']

        for k in requiredKeys:
            if k not in data:
                raise RuntimeError('Key missing in incident data: %s'%k)

        self.data = data # Store a copy of the original data from this object was constructed
        self.__dict__.update(data.iteritems())
        self.addAttr()

    def addAttr(self):
        self.UnitId = self.UnitName + self.UnitType
        self.cleanTimes()

        # Split the station name into a station name and station description.
        # The station description has information about which entrance the escalator/elevator
        # is located.
        self.StationDesc = ''
        stationName = self.StationName
        if ',' in stationName:
            sname, sdesc = stationName.split(',', 1)
            self.StationName = sname.strip()
            self.StationDesc = sdesc.strip()

    def cleanTimes(self):
        attrs = ['DateOutOfServ', 'TimeOutOfService', 'DateUpdated']
        if not all(hasattr(self, a) for a in attrs):
            return

        # Clean up the out of service and update times
        outOfServiceDate = utils.parseMetroDate(self.DateOutOfServ)
        outOfServiceTime = utils.parseMetroTime(self.TimeOutOfService)
        self.TimeOutOfService = datetime.combine(date=outOfServiceDate, time=outOfServiceTime)
        self.TimeUpdated = utils.parseMetroDatetime(self.DateUpdated)

        del self.DateUpdated
        del self.DateOutOfServ

    def isElevator(self):
        return self.UnitType == 'ELEVATOR'

    def isEscalator(self):
        return self.UnitType == 'ESCALATOR'

    def notBroken(self):
        categories = ('PREV. MAINT. INSPECTION', 'SAFETY INSPECTION', 'SCHEDULED SUPPORT', 'REHAB/MODERNIZATION', 'TURNED OFF/WALKER')
        return self.SymptomDescription in categories

    def isInspection(self):
        categories = ('PREV. MAINT. INSPECTION', 'SAFETY INSPECTION')
        return self.SymptomDescription in categories

    def isWalker(self):
        return self.SymptomDescription == 'TURNED OFF/WALKER'

    def isBroken(self):
        return not (self.notBroken())

    def __getitem__(self, k):
        return getattr(self, k)