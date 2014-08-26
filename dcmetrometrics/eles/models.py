"""
Models for eles data.
"""

from mongoengine import *
from operator import attrgetter
from ..common.metroTimes import TimeRange, UTCToLocalTime, toUtc
from .defs import symptomToCategory, SYMPTOM_CHOICES
from ..common import dbGlobals
from .misc_utils import *
from datetime import timedelta
import sys

import logging
logger = logging.getLogger('ELESApp')

class WebJSONMixin(object):

  def to_web_json(self):
    
    fields = getattr(self, 'web_json_fields', [])

    return dict((k, getattr(self, k, None)) for k in fields)

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

  symptom_code = IntField(required=False)
  description = StringField(db_field = 'symptom_desc', required = True, unique = True)
  category = StringField(required=True, choices = SYMPTOM_CHOICES)
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
                        'elevators': []}
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

  meta = {'collection' : 'escalators',
          'indexes': ['unit_id', 'station_code']}

  web_json_fields = ['unit_id', 'station_code', 'station_name',
                     'station_desc', 'esc_desc', 'unit_type',
                     'key_statuses']

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
    has_key_statuses = KeyStatuses.objects(unit = unit).count() > 0
    if status_count == 0:

        if curTime is None:
          curTime = datetime.now() 

        G = dbGlobals.G()

        
        first_status = UnitStatus(escalator_id = unit.id,
                                  time = curTime - timedelta(seconds=1),
                                  tickDelta = 0,
                                  symptom_code = G.OPERATIONAL)
        first_status.denormalize()
        first_status.save()

        logger.info("Saving first status for unit:\n" + str(first_status))

        unit.compute_key_statuses()
        # key_statuses = KeyStatuses(unit = unit)
        # key_statuses.lastOperationalStatus = first_status
        # key_statuses.lastStatus = first_status
        # key_statuses.save()

    elif not has_key_statuses:
      # Compute key statuses from the unit's history.
      logger.info("Could not find a key status entry for unit %s. Building one from the unit's status history\n"%unit.id)
      unit.compute_key_statuses()

  def get_statuses(self, *args, **kwargs):
    """
    Get statuses for the given unit.
    """
    return self._get_unit_statuses(object_id = self.pk, *args, **kwargs)

  @staticmethod
  def _get_unit_statuses(object_id=None, start_time = None, end_time = None):
    """
    Get statuses for a single escalator or elevator unit.
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

    # This call is no longer necessary, because db is denormalized
    #add_status_attributes(statuses)

    return statuses

  def compute_key_statuses(self):
      """
      Compute or recompute the KeyStatuses for a unit.
      Save the KeyStatuses doc and return it.

      If the key statuses have already been computed,
      use the KeyStatuses.update method to simply update
      the existing KeyStatuses record with the latest escalator
      status.
      """
      statuses = self.get_statuses()

      if not statuses:
        return None

      key_statuses = KeyStatuses.select_key_statuses(statuses)

      try:
        # If a KeyStatuses record already exists for this unit, delete it.
        old_key_statuses = KeyStatuses.objects(unit = self).get()
        old_key_statuses.delete()
        logger.info("Deleting existing key statuses entry for unit: " + self.unit_id)
      except DoesNotExist:
        pass

      logger.info("Saving key statuses entry for unit: " + self.unit_id)
      key_statuses.save()
      
      return key_statuses

  def get_key_statuses(self):
      """Return the KeyStatus for this unit by database lookup.
      """
      try:
        key_statuses = KeyStatuses.objects(unit = self).get().select_related()
        return key_statuses
      except DoesNotExist:
        return None

  @property
  def key_statuses(self):
    return self.get_key_statuses()
  


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
  unit = ReferenceField(Unit, required=True, db_field='escalator_id')
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

  symptom_description = StringField()
  symptom_category = StringField(choices=SYMPTOM_CHOICES)

  update_type = StringField(choices = ('Off', 'On', 'Break', 'Fix', 'Update'))



  #######################

  meta = {'collection' : 'escalator_statuses',
          'index' : [('escalator_id', '-time')]}

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
  meta = {'collection' : 'escalator_appstate'}

  def __init__(self, *args, **kwargs):
    kwargs['id'] = 1
    super(self, EscalatorAppState).__init__(*args, **kwargs)

class KeyStatuses(WebJSONMixin, Document):

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
  unit = ReferenceField(Unit, required=True, unique = True)
  lastFixStatus = ReferenceField(UnitStatus) # The oldest operational status which is more recent than lastBreakStatus.
  lastBreakStatus = ReferenceField(UnitStatus) # Mostrecent broken status which has been fixed.
  lastInspectionStatus = ReferenceField(UnitStatus) # Most recent inspection status
  lastOperationalStatus = ReferenceField(UnitStatus) # Most recent operational status
  currentBreakStatus = ReferenceField(UnitStatus) # The oldest broken status which is more recent than the lastOperationalStatus.
  lastStatus = ReferenceField(UnitStatus, required = True) # The most recent status
  
  #################################
  meta = {'collection' : 'key_statuses',
          'indexes': ['unit']
  }

  web_json_fields = ['lastFixStatus', 'lastBreakStatus', 'lastInspectionStatus',
  'lastOperationalStatus', 'currentBreakStatus', 'lastStatus']


  def update(self, unit_status):
    """
    Update a unit's key status record with a new unit status.
    """

    # Check that the unit_status is for the same unit.
    if not (unit_status.unit_id == self.unit.unit_id):
      raise RuntimeError("unit_status's unit does not match KeyStatuses unit")

    if (unit_status != self.lastStatus) and \
       (unit_status.symptom_description == self.lastStatus.symptom_description):
      raise RuntimeError("unit_status is different than lastStatus, but has same symptom id!")

    # Check if there has been a change in status
    if unit_status.symptom_description == self.lastStatus.symptom_description:
      return

    # Update the end_time of the previous status.
    self.lastStatus.end_time = unit_status.time
    self.lastStatus.save()

    if unit_status.symptom_category == 'ON':
      
      self.lastOperationalStatus = unit_status

      if self.currentBreakStatus:
        # This new status is a "fix" which resolves the current break.
        self.lastBreakStatus = self.currentBreakStatus
        self.currentBreakStatus = None
        self.lastFixStatus = unit_status
        unit_status.update_type = 'Fix'
      else:
        unit_status.update_type = 'On'


    elif unit_status.symptom_category == 'BROKEN':
      self.lastBrokenStatus = unit_status

      if not self.currentBreakStatus:
        # This is a new break.
        self.currentBreakStatus = unit_status
        unit_status.update_type = 'Break'
      else:
        unit_status.update_type = 'Update'


    elif unit_status.symptom_category == 'INSPECTION':

      self.lastInspectionStatus = unit_status

      if self.lastStatus.symptom_category == "ON":
        unit_status.update_type = 'Off'
      else:
        unit_status.update_type = 'Update'

    elif unit_status.symptom_category == 'OFF':

      if self.lastStatus.symptom_category == "ON":
        unit_status.update_type = "Off"
      else:
        unit_Status.update_type = "Update"


    self.lastStatus = unit_status
    unit_status.save()
    self.save()


  @classmethod
  def get_last_symptoms(cls, unit_ids = None):
    if unit_ids:
      q = cls.objects(unit__in = list(unit_ids)).scalar('unit', 'lastStatus')
    else:
      q = cls.objects.scalar('unit', 'lastStatus')

    d = {}
    for unit, status in q:
      if status is None:
        d[unit.unit_id] = 'OPERATIONAL'
      else:
        d[unit.unit_id] = status.symptom.pk

    return d

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
    escids = set(s.unit.pk for s in statuses)
    if len(escids) > 1:
        raise RuntimeError('get_key_statuses: received status list for multiple escalators!')

    unit_pk = escids.pop()

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

    return cls(unit = unit_pk, **data)

