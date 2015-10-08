"""
eles.incident

class Incident: An item on the WMATA list of escalator outages.
"""


from ..common.utils import *
from ..common import utils
from datetime import date, datetime, time
from ..common.metroTimes import parse_iso_time
import pprint

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

        # requiredKeys = ['SymptomDescription',
        #                 'LocationDescription',
        #                 'UnitName',
        #                 'UnitType',
        #                 'SymptomCode',
        #                 'StationName',
        #                 'StationCode']

        # for k in requiredKeys:
        #     if k not in data:
        #         raise RuntimeError('Key missing in incident data: %s'%k)

        self._data = data # Store a copy of the original data from this object was constructed
        for k,v in data.iteritems():
            setattr(self, k, v)
        #self.__dict__.update(data.iteritems())
        self.addAttr()

    def addAttr(self):
        """
        Add additional attributes that are not in the MetroAPI:
            - StationName
            - StationDesc
        Split the station name into astation name and station description.
        The station description has information about which entrance the escalator/elevator
        is located.
        """
        self.UnitId = self.UnitName + self.UnitType
        self.cleanTimes()

        self.StationDesc = ''
        if not self.StationName:
            self.StationName = ''

        stationName = self.StationName
        if ',' in stationName:
            sname, sdesc = stationName.split(',', 1)
            self.StationName = sname.strip()
            self.StationDesc = sdesc.strip()

    def cleanTimes(self):
        """
        Convert the times from string to datetimes.
        """
        attrs = ['DateOutOfServ', 'DateUpdated']
        if not all(hasattr(self, a) for a in attrs):
            return

        # Convert the DateOutOfServe and DateUpdated fields
        self.DateOutOfServ = parse_iso_time(self.DateOutOfServ)
        self.DateUpdated = parse_iso_time(self.DateUpdated)


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

    def __str__(self):
        return pprint.pformat(self._data)

