"""
Models for eles data.
"""

from mongoengine import *
from operator import attrgetter
from ..common.metroTimes import TimeRange, UTCToLocalTime, toUtc, tzny, utcnow, dateToOpen
from ..common.WebJSONMixin import WebJSONMixin
from ..common.utils import gen_days
from .defs import symptomToCategory, SYMPTOM_CHOICES
from ..common import dbGlobals
from .misc_utils import *
from .StatusGroup import StatusGroup

from datetime import timedelta, datetime, date
import sys


import logging
logger = logging.getLogger('ELESApp')




class KeyStatuses(WebJSONMixin, EmbeddedDocument):

  """
  This record summarizes the most recent key statuses for a Unit.
  These key statuses are used to figure out when the unit was last inspected, last broken, or
  last fixed.

  Definitions:

    - lastFixStatus: The oldest operational status which follows the most recent break
    - lastBreakStatus: The most recent broken status which has been fixed.
    - lastInspectionStatus: The last inspection status
    - lastOperationalStatus: The most recent operational status
    - lastStatus: The most recent status
    - lastBrokenStatus: The most recent broken status (whether or not it has been fixed).
    - currentBreakStatus: The oldest broken status which is more recent than the lastOperationalStatus.
                          This should be None if the escalator has been fixed since it's last break.

      Note: If there is a transition between broken states, such as :
      ... OPERATIONAL -> CALLBACK/REPAIR -> MINOR REPAIR -> OPERATIONAL,
      then:

        - the lastBreakStatus is that of the CALLBACK/REPAIR, since it is the
          first broken status in the stretch of brokeness. (This is when the break happened).
        - the lastBrokenStatus status is MINOR REPAIR, since it is the most recent broken
          status

  These key statuses can be used to determine things such as:
    
    Q1: When an escalator is fixed, how long was it down for?
    A1: Check the lastOperationalStatus.

    Q2: An escalator is now operational. It's last status was inspection. Should this new status count as a fix?
    A2: Check if there is a currentBreakStatus. If so, then  this should count as a fix.
  """
  unit_id = StringField(required = True)
  lastFixStatus = ReferenceField('UnitStatus') # The oldest operational status which is more recent than lastBreakStatus.
  lastBreakStatus = ReferenceField('UnitStatus') # Mostrecent broken status which has been fixed.
  lastInspectionStatus = ReferenceField('UnitStatus') # Most recent inspection status
  lastOperationalStatus = ReferenceField('UnitStatus') # Most recent operational status
  currentBreakStatus = ReferenceField('UnitStatus') # The oldest broken status which is more recent than the lastOperationalStatus.
  lastStatus = ReferenceField('UnitStatus', required = True) # The most recent status
  
  web_json_fields = ['lastFixStatus', 'lastBreakStatus', 'lastInspectionStatus',
  'lastOperationalStatus', 'currentBreakStatus', 'lastStatus']


  @classmethod
  def get_last_symptoms(cls, unit_ids = None):
    raise RunTimeError("This method is deprecated!")
    # if unit_ids:
    #   q = cls.objects(unit__in = list(unit_ids)).scalar('unit', 'lastStatus')
    # else:
    #   q = cls.objects.scalar('unit', 'lastStatus')

    # d = {}
    # for unit, status in q:
    #   if status is None:
    #     d[unit.unit_id] = 'OPERATIONAL'
    #   else:
    #     d[unit.unit_id] = status.symptom.pk

    # return d

  @classmethod
  def select_key_statuses(cls, statuses):
    """
      This is a helper method.

      # From a list of statuses, select key statuses
      # -lastFix: The oldest operational status which follows the most recent break
      # -lastBreak: The most recent broken status which has been fixed.
      # -lastInspection: The last inspection status
      # -lastOp: The most recent operational status
      # -lastStatus: The most recent status
      # Note: If there is a transition between broken states, such as :
      # ... OPERATIONAL -> CALLBACK/REPAIR -> MINOR REPAIR -> OPERATIONAL,
      # then the lastBreak status is that of the CALLBACK/REPAIR, since it is the
      # first broken status in the stretch of brokeness.

    Return a KeyStatuses record, without saving.
    """

    checkAllTimesNotNaive(statuses)

    # Check that these statuses concern a single escalator
    escids = set(s.unit.unit_id for s in statuses)
    if len(escids) > 1:
        raise RuntimeError('get_key_statuses: received status list for multiple escalators!')

    unit_id = escids.pop()

    # Sort statuses by time in descending order
    statusesRevCron = sorted(statuses, key = attrgetter('time'), reverse=True)
    statusesCron = statusesRevCron[::-1]
    statuses = statusesRevCron

    # Add additional attributes to all statuses
    #add_status_attributes(statuses)

    # Organize the operational statuses and breaks.
    # Associate each operational status with the next break which follows it
    # Associate each break with the next operational status which follows it
    ops = [rec for rec in statuses if rec.symptom_category == 'ON']
    opTimes = [rec.time for rec in ops]
    breaks = [rec for rec in statuses if rec.symptom_category == 'BROKEN']
    breakTimes = [rec.time for rec in breaks]

    breakTimeToFix = {}
    opTimeToNextBreak = {}
    for bt in breakTimes:
        breakTimeToFix[bt] = get_first_status_since(ops, bt)
    for opTime in opTimes:
        opTimeToNextBreak[opTime] = get_first_status_since(breaks, opTime)

    lastOp = ops[0] if ops else None
    lastStatus = statuses[0] if statuses else None

    def getStatus(timeToStatusDict):
        keys = sorted(timeToStatusDict.keys(), reverse=True)
        retVal = None
        for k in keys:
            retVal = timeToStatusDict[k]
            if retVal is not None:
                return retVal
        return retVal

    # Get the most recent break which has been fixed
    lastBreak = getStatus(opTimeToNextBreak)

    # Get the most recent fix
    lastFix = getStatus(breakTimeToFix)

    # Get the break since the most recent operational status, if it exists.
    currentBreak = breaks[0] if breaks else None
    if currentBreak and lastOp and currentBreak.time < lastOp.time:
        currentBreak = None 

    # Get the last inspection status
    lastInspection = get_one(rec for rec in statuses if rec.symptom_category == 'INSPECTION')

    data = { 'lastFixStatus' : lastFix,
            'lastInspectionStatus' : lastInspection,
            'lastBreakStatus': lastBreak,
            'lastOperationalStatus' : lastOp,
            'lastStatus' : lastStatus,
            'currentBreakStatus' : currentBreak
    }

    return cls(unit_id = unit_id, **data)


class UnitPerformancePeriod(WebJSONMixin, EmbeddedDocument):
  """
  A performance summary for a unit over a time period.
  """
  unit_id = StringField(required = True)
  created = DateTimeField(default = utcnow) # Creation time of the document.
  start_time = DateTimeField(required = True)
  end_time = DateTimeField(required = True)
  availability = FloatField(required = True)
  broken_time_percentage = FloatField(required = True)
  num_breaks = IntField(required = True)
  num_inspections = IntField(required = True)
  day_to_break_count = DictField(required = False)
  break_days = ListField(StringField(), required = False) # Days where the escalator was broken

  web_json_fields = ['unit_id', 'start_time', 'end_time', 'availability',
    'broken_time_percentage', 'num_breaks', 'num_inspections',
    'break_days', 'day_to_break_count']


class UnitPerformanceSummary(WebJSONMixin, EmbeddedDocument):
  """
  A performance summary for a unit over several time periods.
  """
  unit = ReferenceField('Unit', required = True, primary_key = True)
  unit_id = StringField(required = True, unique = True)

  # Performance summaries
  one_day = EmbeddedDocumentField(UnitPerformancePeriod)
  three_day = EmbeddedDocumentField(UnitPerformancePeriod)
  seven_day = EmbeddedDocumentField(UnitPerformancePeriod)
  fourteen_day = EmbeddedDocumentField(UnitPerformancePeriod)
  thirty_day = EmbeddedDocumentField(UnitPerformancePeriod)
  all_time = EmbeddedDocumentField(UnitPerformancePeriod)

  web_json_fields = ['one_day', 'three_day', 'seven_day', 'fourteen_day',
                     'thirty_day', 'all_time']


class SymptomCodeOld(Document):
  """
  The different states an escalator can be in.
  """

  id = IntField(primary_key = True, db_field = '_id')
  description = StringField(db_field = 'symptom_desc', required=True)
  category = StringField(choices = SYMPTOM_CHOICES)
  meta = {'collection' : 'symptom_codes_old'}

  def __str__(self):
    output = ''
    output += '\tcode: %s\n'%(self.pk)
    output += '\tdescription: %s\n'%(self.description)
    return output

  def make_new_format(self):
    new = SymptomCode(symptom_code = self.id,
      description = self.description,
      category = self.category)
    return new

  @classmethod
  def add(cls, code, description):
    code = cls(pk=int(code),
               description=description, 
               category = symptomToCategory[description])
    code.save()
    return code

class SymptomCode(Document):
  """
  The different states an escalator can be in.
  """

  symptom_code = IntField(required = False)
  description = StringField(db_field = 'symptom_desc', required = True, unique = True)
  category = StringField(required = True, choices = SYMPTOM_CHOICES)
  meta = {'collection' : 'symptom_codes'}

  def __str__(self):
    output = ''
    output += '\id: %s\n'%(self.pk)
    output += '\tdescription: %s\n'%(self.description)
    output += '\tcategory: %s\n'%(self.category)
    return output

  @classmethod
  def add(cls, description):
    try:
      symptom = cls(description=description, 
                 category = symptomToCategory[description])
      symptom.save()
      logger.info("Saving new symptom: " + description)
    except NotUniqueError:
      pass

class Station(WebJSONMixin, Document):
  """
  A WMATA Station
  """
  code = StringField(required = True, primary_key = True)
  long_name = StringField(required = True)
  medium_name = StringField(required = True)
  short_name = StringField(required = True)
  lines = ListField(StringField(choices = ('RD', 'OR', 'YL', 'GR', 'BL', 'SV'))) # Lines for this station platform
  all_lines = ListField(StringField(choices = ('RD', 'OR', 'YL', 'GR', 'BL', 'SV'))) # Lines for all platforms at this station
  all_codes = ListField(StringField()) # Station codes for all the platforms at this station
  

  meta = {'collection' : 'stations',
          'indexes': ['long_name']}

  web_json_fields = ['code', 'long_name', 'short_name',
                     'medium_name', 'lines', 'all_lines', 'all_codes']


  def get_shared_stations(self):
    """Get stations that are shared with this one. Return as a list,
    including this station.
    """
    #shared = list(Station.objects(long_name = self.long_name))
    shared = list(Station.objects(code__in = self.all_codes))
    return shared

  @classmethod
  def add(cls, code, long_name, medium_name, short_name, lines, all_lines, all_codes):
    station = Station(code, long_name, medium_name, short_name, lines, all_lines, all_codes)
    station.save()
    return station

  def _get_units(self, shared = True, escalators = True, elevators = True):
    """Get units for a station.
    By default this gets all shared units (i.e. all stations with the same name, even if code
      differs)
    """
    if shared:
      shared_stations = self.get_shared_stations()
      all_codes = [s.code for s in shared_stations]
    else:
      all_codes = [self.code]

    ret_units = []

    units = Unit.objects(station_code__in = all_codes)
    escalator_units = (u for u in units if u.unit_type == "ESCALATOR")
    elevator_units = (u for u in units if u.unit_type == "ELEVATOR")

    if escalators:
      ret_units.extend(escalator_units)

    if elevators:
      ret_units.extend(elevator_units)

    return ret_units

  def get_shared_units(self, **kwargs):
    """
    Get units for all stations that share this name. Transfer stations
    with multiple platforms (i.e. Fort Totten, Gallery Place, L'Enfant, MetroCenter, etc.)
    will have multiple station docs.
    """
    return self._get_units(shared = True, **kwargs)

  def get_units(self, **kwargs):
    return self._get_units(shared = False, **kwargs)

  def get_escalators(self):
    return self._get_units(shared = False, escalators = True, elevators = False)

  def get_elevators(self):
    return self._get_units(shared = False, escalators = False, elevators = True)

  def get_recent_statuses(self, n = 20):
    """
    Get recent statuses for this station
    """
    q = UnitStatus.objects(station_code__in = self.all_codes).order_by('-time').limit(n)
    return list(q)

  @classmethod
  def get_station_directory(cls):

    """Form the station directory. Merge stations that share the same name 
    (i.e. both platforms at Fort Totten, Gallery Place, etc.)
    """
    all_stations = list(cls.objects)  
    code_to_name = dict((s.code, s.long_name) for s in all_stations)
    code_to_station = dict((s.code, s) for s in all_stations)
    all_units = list(Unit.objects)
    # for u in all_units:
    #   u.key_statuses = u.get_key_statuses()

    # Collection units by station names
    station_to_data = {}
    for station in all_stations:
      station_name = station.long_name
      station_data = station_to_data.get(station_name, None)
      if not station_data:
        station_data = {'stations': [station], 
                        'escalators': [],
                        'elevators': [],
                        'recent_statuses': station.get_recent_statuses(20)}
      else:
        station_data['stations'].append(station)
      station_to_data[station_name] = station_data


    for u in all_units:

      station_name = code_to_name[u.station_code]
      station = code_to_station[u.station_code]
      station_data = station_to_data.get(station_name, None)

      # station_data should not be None, but check anyway
      if station_data:
        # Add the unit
        if u.is_escalator():
          station_data['escalators'].append(u)
        elif u.is_elevator():
          station_data['elevators'].append(u)

        station_to_data[station_name] = station_data

    # Sort the units by their ids.
    for station_name, station_data in station_to_data.iteritems():
      station_data['escalators'] = sorted(station_data['escalators'], key = lambda s: s.unit_id)
      station_data['elevators'] = sorted(station_data['elevators'], key = lambda s: s.unit_id)
    
    return station_to_data


class Unit(WebJSONMixin, Document):
  """
  An escalator or an elevator.
  """
  unit_id = StringField(required=True, unique=True)
  station_code = StringField(required=True)
  station_name = StringField(required=True)
  station_desc = StringField(required=False)
  esc_desc = StringField(required=True)
  unit_type = StringField(required=True, choices=('ESCALATOR', 'ELEVATOR'))
  key_statuses = EmbeddedDocumentField(KeyStatuses)
  performance_summary = EmbeddedDocumentField(UnitPerformanceSummary)
  
  meta = {'collection' : 'escalators',
          'indexes': ['unit_id', 'station_code']}

  web_json_fields = ['unit_id', 'station_code', 'station_name',
                     'station_desc', 'esc_desc', 'unit_type',
                     'key_statuses', 'performance_summary',
                     'statuses']

  def is_elevator(self):
    return self.unit_type == 'ELEVATOR'

  def is_escalator(self):
    return self.unit_type == 'ESCALATOR'

  def __str__(self):
    keys = ['unit_id', 'station_code', 'station_name',
            'station_desc', 'esc_desc', 'unit_type']
    output = ''
    for k in keys:
      output += '\t%s: %s\n'%(k, getattr(self, k, 'N/A'))
    return output

  @classmethod
  def add(cls, curTime = None, **kwargs):
    """
    Add a unit to the database if it does not already exist.
    If the unit is being added for the first time, create an initial
    operational UnitStatus entry.

    If the unit already exists and a status already exists,
    do nothing.
    """
    unit_id = kwargs['unit_id']

    try:

      unit = Unit.objects.get(unit_id = unit_id)

    except DoesNotExist:
      logger.info("Adding Unit to DB: " + unit_id)
      unit = cls(**kwargs)
      unit.save()

    # Add a new entry to the escalator_statuses collection if necessary
    status_count = UnitStatus.objects(unit = unit).count()
    has_key_statuses = unit.key_statuses is not None
    has_performance_summary = unit.performance_summary is not None

    updated_unit = False

    if status_count == 0:

        if curTime is None:
          curTime = datetime.now() 

        G = dbGlobals.G()

        
        first_status = UnitStatus(unit = unit,
                                  time = curTime - timedelta(seconds=1),
                                  tickDelta = 0,
                                  symptom_code = G.OPERATIONAL)
        first_status.denormalize()
        first_status.save()

        logger.info("Saving first status for unit:\n" + str(first_status))

        unit.compute_key_statuses()
        unit.compute_performance_summary()

        updated_unit = True

    else:

      if not has_key_statuses:
        # Compute key statuses from the unit's history.
        logger.info("Could not find a key status entry for unit %s. Building one from the unit's status history\n"%unit.id)
        unit.compute_key_statuses()
        updated_unit = True

      if not has_performance_summary:
        logger.info("Could not find a performance summary for unit %s. Building one from the unit's status history\n"%unit.id)
        unit.compute_performance_summary()
        updated_unit = True

    if updated_unit:
      unit.save()


  def get_statuses(self, *args, **kwargs):
    """
    Get statuses for the given unit.
    """
    return self._get_unit_statuses(object_id = self.pk, *args, **kwargs)

  def compute_performance_summary(self, statuses = None, save = False, end_time = None):
    """
    Compute or recompute the historical performance summary for a unit.
    """

    # If a record already exists, delete it.
    self.performance_summary = None

    debug_start_time = datetime.now()

    if not statuses:
      statuses = self.get_statuses() # This resturn statuses in descending order, most recent first
    statuses = sorted(statuses, key = attrgetter('time'))

    logger.info("Computing performance summary for unit: %s"%self.unit_id)
    logger.debug("Unit {0} has {1} statuses".format(self.unit_id, len(statuses)))
    if not statuses:
      logger.warning("No statuses for unit %s! Not computing performance summary."%self.unit_id)
      return None

    if end_time is None:
      end_time = utcnow()

    start_times = [('one_day', end_time - timedelta(days = 1)),
                   ('three_day', end_time - timedelta(days = 3)),
                   ('seven_day', end_time - timedelta(days = 7)),
                   ('fourteen_day', end_time - timedelta(days = 14)),
                   ('thirty_day', end_time - timedelta(days = 30)),
                   ('all_time', statuses[0].time)]

    ups = UnitPerformanceSummary(unit = self, unit_id = self.unit_id)

    for key, start_time in start_times:
      sg = StatusGroup(statuses, start_time, end_time)
      upp = UnitPerformancePeriod(unit_id = self.unit_id,
                                 start_time = start_time,
                                 end_time = end_time,
                                 availability = sg.availability,
                                 broken_time_percentage = sg.brokenTimePercentage,
                                 num_breaks = len(sg.breakStatuses),
                                 num_inspections = len(sg.inspectionStatuses)
                                 )

      # To avoid redundancy, only set break_days and day_to_break_count
      # for the all_time performance summary:
      if(key == 'all_time'):

          day_to_break_count = sg.day_to_break_count

          # This throws a ValidationError in MongoEngine. Likely a MongoEngine Bug. Instead, save a simpler dict to the DictField.
          # upp.day_to_break_count = day_to_break_count 
          
          day_to_break_count_str_keys = dict( (d.strftime('%Y-%m-%d'), c) for
             d,c in day_to_break_count.iteritems())

          upp.day_to_break_count = day_to_break_count_str_keys
  
          upp.break_days = [ d.strftime('%Y-%m-%d')  for d in sg.break_days ]

      setattr(ups, key, upp)

    self.performance_summary = ups

    if save:
      self.save()

    debug_end_time = datetime.now()
    delta = (debug_end_time - debug_start_time).total_seconds()
    logger.debug("Unit {0}: {1:.3f} sec {2:.3f} factor.".format(self.unit_id, delta, delta/len(statuses)))

    return ups

  def update(self, unit_status):
    """
    Update a unit's history with a new unit status.

    This will update the unit's key_status record.
    """

    if self.key_statuses is None:
      self.compute_key_statuses()

    key_statuses = self.key_statuses

    # Check that the unit_status is for the same unit.
    if not (unit_status.unit_id == self.unit_id):
      raise RuntimeError("unit_status's unit does not match this unit!")

    if (unit_status != key_statuses.lastStatus) and \
       (unit_status.symptom_description == key_statuses.lastStatus.symptom_description):
      raise RuntimeError("unit_status is different than lastStatus, but has same symptom id!")

    # Check if there has been a change in status
    # If not, do nothing.
    if unit_status.symptom_description == key_statuses.lastStatus.symptom_description:
      return

    if unit_status.symptom_category == 'ON':
      
      key_statuses.lastOperationalStatus = unit_status

      if key_statuses.currentBreakStatus:
        # This new status is a "fix" which resolves the current break.
        key_statuses.lastBreakStatus = key_statuses.currentBreakStatus
        key_statuses.currentBreakStatus = None
        key_statuses.lastFixStatus = unit_status
        unit_status.update_type = 'Fix'
      else:
        unit_status.update_type = 'On'


    elif unit_status.symptom_category == 'BROKEN':
      key_statuses.lastBrokenStatus = unit_status

      if not key_statuses.currentBreakStatus:
        # This is a new break.
        key_statuses.currentBreakStatus = unit_status
        unit_status.update_type = 'Break'
      else:
        unit_status.update_type = 'Update'


    elif unit_status.symptom_category == 'INSPECTION':

      key_statuses.lastInspectionStatus = unit_status

      if key_statuses.lastStatus.symptom_category == "ON":
        unit_status.update_type = 'Off'
      else:
        unit_status.update_type = 'Update'

    elif unit_status.symptom_category == 'OFF':

      if key_statuses.lastStatus.symptom_category == "ON":
        unit_status.update_type = "Off"
      else:
        unit_status.update_type = "Update"

    # Update the end_time of the previous status.
    key_statuses.lastStatus.end_time = unit_status.time
    key_statuses.lastStatus.save()

    # Update the keyStatus with the new status.
    key_statuses.lastStatus = unit_status
    unit_status.save()

    # Save the updated key_statuses to self.
    self.key_statuses = key_statuses
    self.save()


  @staticmethod
  def _get_unit_statuses(object_id=None, start_time = None, end_time = None):
    """
    Get statuses for a single escalator or elevator unit, in descending order of time.
    start_time and end_time can be used to return statuses for a given time period.

    If start_time or end_time are provided, the status list is padded
    with statuses that preceed and follow the statuses in the time range in
    order to provide context.

    It's recommended that all statuses for a unit are retrieved via this method,
    because it will make status timezones non-naive.
    """

    # Convert start_time and end_time to utcTimeZone, if necessary
    if start_time is not None:
        start_time = toUtc(start_time)
    if end_time is not None:
        end_time = toUtc(end_time)

    # Find latest statuses for this escalator
    query = {'unit' : object_id}
    if start_time is not None:
        query['time__gte'] = start_time
    if end_time is not None:
        query['time__lte'] = end_time

    statuses = list(UnitStatus.objects(**query).order_by('-time').select_related())

    # If start_time is specified, give all statuses from first operational
    # status which preceeds start_time
    if start_time is not None and ((not statuses) or (statuses[-1].symptom.pk != OP_CODE)):
        firstStatusTime = start_time
        query = {'unit' : object_id,
                 'time__lt' : firstStatusTime}
        c = UnitStatus.objects(**query).order_by('-time').select_related()
        preceeding = []
        for s in c:
            preceeding.append(s)
            if s.symptom.pk == OP_CODE:
                break
        statuses.extend(preceeding)

    # If end_time is specified, give all statuses after the first
    # operational status which follows end_time
    if end_time is not None and ((not statuses) or (statuses[0].symptom.pk != OP_CODE)):
        lastStatusTime = end_time
        query = {'unit' : object_id,
                 'time__gt' : lastStatusTime}
        c = UnitStatus.objects(**query).order_by('+time').select_related()
        following = []
        for s in c:
            following.append(s)
            if s.symptom.pk == OP_CODE:
                break
        # Following are in ascending order. Reverse the order to make it descending.
        following = following[::-1]
        statuses = following + statuses

    # Add tzinfo to all status
    for status in statuses:
        status._add_timezones()

    return statuses

  def compute_key_statuses(self, save = False):
      """
      Compute or recompute the KeyStatuses for a unit.
      Save the KeyStatuses doc and return it.

      If the key statuses have already been computed,
      use the KeyStatuses.update method to simply update
      the existing KeyStatuses record with the latest escalator
      status.
      """
      statuses = self.get_statuses()
      self.key_statuses = None

      if not statuses:
        return None

      logger.info("Computing key statuses entry for unit: " + self.unit_id)
      self.key_statuses = KeyStatuses.select_key_statuses(statuses)
      if save:
        self.save()
      return self.key_statuses

  def compute_daily_service_reports(self, save = False, statuses = [],
     start_day = date(2013, 6, 1),
     last_day = None):

    if last_day is None:
      last_day = date.today() + timedelta(days=1)

    if not statuses:
      statuses = self.get_statuses()

    docs = []
    for day in gen_days(start_day, last_day):

      logger.info("Computing daily service report for unit %s on %s"%(self.unit_id,
         day.strftime("%Y-%m-%d")))

      dsr = DailyServiceReport.compute_for_unit(self, day, statuses = statuses)

      docs.append(dsr)

    if save:

      # By default we will erase any existing daily service reports on these days
      existing = DailyServiceReport.objects(day__gte = start_day.strftime("%Y-%m-%d"),
                                            day__lt = last_day.strftime("%Y-%m-%d"),
                                            unit_id = self.unit_id).no_cache()
      logger.info("Removing %i existing daily service reports for unit %s"%(existing.count(), self.unit_id))
      existing.delete()

      DailyServiceReport.objects.insert(docs)

    return docs


#############################################
# Old format for UnitStatus, with reference to symptoms in old format.
class UnitStatusOld(WebJSONMixin, Document):
  """
  Escalator or elevator status.
  """
  unit = ReferenceField(Unit, required=True, db_field='escalator_id')
  time = DateTimeField(required=True)
  end_time = DateTimeField()
  metro_open_time = FloatField() # Duration of status for which metro was open (seconds)
  symptom = ReferenceField(SymptomCodeOld, required=True, db_field='symptom_code')
  tickDelta = FloatField(required=True, default=0.0)

  # Denormalized fields
  unit_id = StringField()
  station_code = StringField()
  station_name = StringField()
  station_desc = StringField()
  esc_desc = StringField()
  unit_type = StringField(choices=('ESCALATOR', 'ELEVATOR'))

  symptom_description = StringField()
  symptom_category = StringField(choices=SYMPTOM_CHOICES)



  #######################

  meta = {'collection' : 'escalator_statuses_old',
          'index' : [('escalator_id', '-time')]}

  web_json_fields = ['unit_id', 'time', 'end_time', 'metro_open_time',
    'tickDelta', 'symptom_description', 'symptom_category']


  def to_new_format(self):
    """Convert to the new UnitStatus format. Leave the symptom field blank"""
    new = UnitStatus(unit = self.unit,
      time = self.time,
      end_time = self.end_time,
      metro_open_time = self.metro_open_time, 
      symptom = None,
      tickDelta = self.tickDelta,
      unit_id = self.unit_id,
      station_code = self.station_code,
      station_name = self.station_name,
      station_desc = self.station_desc,
      esc_desc = self.esc_desc,
      unit_type = self.unit_type,
      symptom_description = self.symptom_description,
      symptom_category = self.symptom_category)
    return new


  def clean(self):
    """
    Convert the time and end_time fields to UTC time zone.
    """
    self.time = toUtc(self.time, allow_naive = True)
    if self.end_time:
      self.end_time = toUtc(self.end_time, allow_naive = True)


  #######################
  def __str__(self):
    keys = ['unit_id', 'station_name', 'station_desc', 'esc_desc', 'unit_type', 'time', 'end_time', 'metro_open_time']
    output = '' 
    output += '\tunit: %s\n'%self.unit_id
    output += '\tsymptom: %s\n'%self.symptom.description
    for k in keys:
      output += '\t%s: %s\n'%(k, getattr(self,k, 'N/A'))
    return output

  def denormalize(self):
    """
    Denormalize by grabbing fields from unit data and symptom data.
    """
    unit = self.unit
    symptom = self.symptom

    self.unit_id = unit.unit_id
    self.station_code = unit.station_code
    self.station_name = unit.station_name
    self.station_desc = unit.station_desc
    self.esc_desc = unit.esc_desc
    self.unit_type = unit.unit_type

    self.symptom_description = symptom.description
    self.symptom_category = symptom.category

  def compute_metro_open_time(self):
    """
    Compute the amount of time for which Metro was open that this status
    lasted. 
    """
    start_time = UTCToLocalTime(self.time)
    end_time = getattr(self, 'end_time', None)
    if end_time:
      end_time = UTCToLocalTime(end_time)
      time_range = TimeRange(start_time, end_time)
      self.metro_open_time = time_range.metroOpenTime

  def _add_timezones(self):
    """
    Make the time and end_time fields non-naive timezones,
    in UTC.

    Timezones are stored as naive UTC datetimes in database,
    but should be used in application logic as non-naive datetimes,
    (i.e. they shoudl have UTC timezone.)
    """
    self.time = toUtc(self.time, allow_naive = True)
    end_time = getattr(self, 'end_time', None)
    if end_time:
      self.end_time = toUtc(self.end_time, allow_naive = True)

#############################################
# New format for UnitStatus, with reference to symptoms in new format.
class UnitStatus(WebJSONMixin, Document):
  """
  Escalator or elevator status.
  """
  unit = ReferenceField('Unit', required=True, db_field='escalator_id')
  time = DateTimeField(required=True)
  end_time = DateTimeField()
  metro_open_time = FloatField() # Duration of status for which metro was open (seconds)
  symptom = ReferenceField(SymptomCode, required=True, db_field='symptom_code')
  tickDelta = FloatField(required=True, default=0.0)

  # Denormalized fields
  unit_id = StringField()
  station_code = StringField()
  station_name = StringField()
  station_desc = StringField()
  esc_desc = StringField()
  unit_type = StringField(choices=('ESCALATOR', 'ELEVATOR'))

  symptom_description = StringField(required = True)
  symptom_category = StringField(choices=SYMPTOM_CHOICES)

  update_type = StringField(choices = ('Off', 'On', 'Break', 'Fix', 'Update'))



  #######################

  meta = {'collection' : 'escalator_statuses',
          'index' : [('escalator_id', '-time'),
                     ('station_code', '-time'),
                     ('time', 'end_time'),
                    ]}

  web_json_fields = ['unit_id', 'time', 'end_time', 'metro_open_time',
    'update_type',
    'tickDelta', 'symptom_description', 'symptom_category']

  def clean(self):
    """
    Convert the time and end_time fields to UTC time zone.
    """
    self.time = toUtc(self.time, allow_naive = True)
    if self.end_time:
      self.end_time = toUtc(self.end_time, allow_naive = True)


  #######################
  def __str__(self):
    keys = ['unit_id', 'station_name', 'station_desc',
    'esc_desc', 'unit_type', 'symptom_description', 'symptom_category',
    'update_type',
    'time', 'end_time', 'metro_open_time']
    output = '' 
    output += '\tunit: %s\n'%self.unit_id
    output += '\tsymptom: %s\n'%self.symptom.description
    for k in keys:
      output += '\t%s: %s\n'%(k, getattr(self,k, 'N/A'))
    return output

  def denormalize(self):
    """
    Denormalize by grabbing fields from unit data and symptom data.
    """
    unit = self.unit
    symptom = self.symptom

    self.unit_id = unit.unit_id
    self.station_code = unit.station_code
    self.station_name = unit.station_name
    self.station_desc = unit.station_desc
    self.esc_desc = unit.esc_desc
    self.unit_type = unit.unit_type

    self.symptom_description = symptom.description
    self.symptom_category = symptom.category

  def compute_metro_open_time(self):
    """
    Compute the amount of time for which Metro was open that this status
    lasted. 
    """
    start_time = UTCToLocalTime(self.time)
    end_time = getattr(self, 'end_time', None)
    if end_time:
      end_time = UTCToLocalTime(end_time)
      time_range = TimeRange(start_time, end_time)
      self.metro_open_time = time_range.metroOpenTime

  def _add_timezones(self):
    """
    Make the time and end_time fields non-naive timezones,
    in UTC.

    Timezones are stored as naive UTC datetimes in database,
    but should be used in application logic as non-naive datetimes,
    (i.e. they shoudl have UTC timezone.)
    """
    self.time = toUtc(self.time, allow_naive = True)
    end_time = getattr(self, 'end_time', None)
    if end_time:
      self.end_time = toUtc(self.end_time, allow_naive = True)


  @property
  def is_active(self):
      return self.end_time is None

  @property
  def start_time(self):
      return self.time


class DailyServiceReport(WebJSONMixin, Document):
  """A daily service report for a unit.
  Compute availability, outage statuses, inspection statuses,
  etc for a Metro Day

  We represent as an EmbeddedDocument, but never actually save it anywhere.
  We could.
  """
  unit_id = StringField(required = True)
  day = StringField(required = True, unique_with = 'unit_id') # "yyyy-mm-dd"
  created = DateTimeField(default = utcnow) # Creation time of the document.
  availability = FloatField(required = True)
  broken_time_percentage = FloatField(required = True)
  num_breaks = IntField(required = True)
  num_inspections = IntField(required = True)
  num_fixes = IntField(required = True)
  statuses = ListField(ReferenceField(UnitStatus))

  meta = { 'indexes' : ['unit_id',
                        'day',
                        ('unit_id', 'day')
            ]
  }

  web_json_fields = ['unit_id', 'day', 'availability', 'broken_time_percentage',
  'num_breaks', 'num_inspections', 'num_fixes', 'statuses']


  @classmethod
  def compute_for_unit(cls, unit, day, statuses = None):

    start_time = dateToOpen(day)
    end_time = dateToOpen(day + timedelta(days=1))

    if not statuses:
      statuses = unit.get_statuses()

    sg = StatusGroup(statuses, start_time, end_time)

    ret = cls()
    ret.unit_id = unit.unit_id
    ret.day = day.strftime("%Y-%m-%d")
    ret.availability = sg.availability
    ret.broken_time_percentage = sg.brokenTimePercentage
    ret.num_breaks = sg.num_breaks
    ret.num_inspections = sg.num_inspections
    ret.num_fixes = sg.num_fixes
    ret.statuses = sg.statuses

    return ret

class UnitTypeServiceReport(WebJSONMixin, EmbeddedDocument):

  availability = FloatField(required = True)
  broken_time_percentage = FloatField(required = True)
  num_breaks = IntField(required = True)
  num_inspections = IntField(required = True)
  num_fixes = IntField(required = True)
  statuses = ListField(ReferenceField(UnitStatus))
  num_units = IntField(required = True) # Number of units contributing to the report


  web_json_fields = ['availability', 'broken_time_percentage',
    'num_breaks', 'num_inspections', 'num_fixes', 'statuses', 'num_units']


  @classmethod
  def from_daily_service_reports(cls, reports):

    doc = cls()

    reports = [r for r in reports if r.statuses] # Only include units that had reports on this day
    doc.num_units = len(reports)
    doc.num_breaks = sum(r.num_breaks for r in reports)
    doc.num_inspections = sum(r.num_inspections for r in reports)
    doc.num_fixes = sum(r.num_fixes for r in reports)
    doc.statuses = [s for r in reports for s in r.statuses if s.symptom_category != "ON"]

    a = sum(r.availability for r in reports)
    b = sum(r.broken_time_percentage for r in reports)
    doc.availability = a/float(doc.num_units) if doc.num_units > 0 else 1.0
    doc.broken_time_percentage = b/float(doc.num_units) if doc.num_units > 0 else 0.0

    return doc


class SystemServiceReport(WebJSONMixin, Document):
  """A daily service report for the system
  Compute availability, outage statuses, inspection statuses,
  etc for a Metro Day

  We represent as an EmbeddedDocument, but never actually save it anywhere.
  We could.
  """

  day = StringField(required = True, unique = True) # "yyyy-mm-dd"
  created = DateTimeField(default = utcnow) # Creation time of the document.

  escalators = EmbeddedDocumentField(UnitTypeServiceReport)
  elevators = EmbeddedDocumentField(UnitTypeServiceReport)

  meta = { 'indexes' : ['day']  }

  web_json_fields = ['day', 'escalators', 'elevators']

  @classmethod
  def compute_for_day(cls, day, reports = None, save = True):
    """
    Compute the system service report by pulling DailyServiceReports
    from the db
    """
    day_string = day.strftime("%Y-%m-%d")

    logger.info("Computing system service report for day %s"%day_string)
    doc = cls()
    doc.day = day_string

    escalator_reports = []
    elevator_reports = []

    if not reports:
      reports = list(DailyServiceReport.objects(day = doc.day))

    if not reports:
      raise RuntimeError('Do not have any daily service reports for day: %s'%doc.day)

    escalator_reports = []
    elevator_reports = []

    for r in reports:
      if 'ESCALATOR' in r.unit_id:
        escalator_reports.append(r)
      else:
        elevator_reports.append(r)

    doc.escalators = UnitTypeServiceReport.from_daily_service_reports(escalator_reports)
    doc.elevators = UnitTypeServiceReport.from_daily_service_reports(elevator_reports)

    if save:
      cls.objects(day = doc.day).delete()
      doc.save()
    return doc



class ElevatorAppState(Document):
  """
  State of the MetroElevators app.
  """
  id = IntField(required=True, default = 1, db_field = '_id', primary_key=True)
  lastRunTime = DateTimeField()
  lastDailyStatsTime = DateTimeField()
  meta = {'collection' : 'elevator_appstate'}

  def __init__(self, *args, **kwargs):
    kwargs['id'] = 1
    super(self, ElevatorAppState).__init__(*args, **kwargs)

class EscalatorAppState(Document):
  """
  State of the MetroEscalators app.
  """
  id = IntField(required=True, default = 1, db_field = '_id', primary_key=True)
  lastRunTime = DateTimeField()
  lastDailyStatsTime = DateTimeField()
  lastPerformanceSummaryTime = DateTimeField()
  meta = {'collection' : 'escalator_appstate'}

  @classmethod 
  def get(cls):
    try:
      obj = cls.objects.get(pk = 1)
    except DoesNotExist:
      obj = cls(id = 1)
      obj.save()

    # Add time zones
    if obj.lastRunTime:
      obj.lastRunTime = toUtc(obj.lastRunTime, allow_naive = True)
    if obj.lastDailyStatsTime:
      obj.lastDailyStatsTime = toUtc(obj.lastDailyStatsTime, allow_naive = True)
    if obj.lastPerformanceSummaryTime:
      obj.lastPerformanceSummaryTime = toUtc(obj.lastPerformanceSummaryTime, allow_naive = True)

    return obj