"""
Script to denormalize the database by adding fields to the unit status records.

This should be imported as a module and not run directly.
"""

from . import utils
utils.fixSysPath()

import sys

from dcmetrometrics.common.dbGlobals import DBG
from dcmetrometrics.eles import dbUtils
from dcmetrometrics.eles.models import Unit, SymptomCode, UnitStatus

def denormalize_unit_statuses():
  """
  Denormalized UnitStatus records by adding status and
  symptom fields to the UnitStatus.

  Also compute end_time and metro_open_time.
  """

  num_units = Unit.objects.count()
  sys.stderr.write("Have %i units\n"%num_units)
  for i, unit in enumerate(Unit.objects):
    sys.stderr.write('Processing unit %s\n (%i of %i)'%(unit.unit_id, i, num_units))
    unit_statuses = UnitStatus.objects(unit = unit).order_by('-time')
    num_statuses = unit_statuses.count()
    unit_statuses.select_related()
    sys.stderr.write('\tHave %i statuses\n'%num_statuses)
    status_after = None
    for status in unit_statuses:
      status.denormalize()
      if status_after:
        status.end_time = status_after.time
        status.compute_metro_open_time()
      status.save()
      status_after = status


def migration_03_2014():
  #denormalize_unit_statuses()
  dbUtils.set_unit_key_statuses()

def migration_07_2014():
  from mongoengine import connect
  from dcmetrometrics.common.globals import * 
  connect('MetroEscalators', alias = "default", host=MONGODB_HOST, port=MONGODB_PORT, username=MONGODB_USERNAME, password=MONGODB_PASSWORD)
  connect("MetroEscalatorsDO", alias = "do", host=MONGODB_HOST, port=MONGODB_PORT,  username=MONGODB_USERNAME, password=MONGODB_PASSWORD)
  

  #denormalize_unit_statuses()
  dbUtils.set_unit_key_statuses()

def add_station_docs():
  """
  Create station documents 
  """
  from dcmetrometrics.common import stations
  from dcmetrometrics.eles.models import Station
  station_codes = stations.codeToName.keys()
  for station_code in station_codes:
    short_name = stations.codeToShortName[station_code]
    long_name = stations.codeToName[station_code]
    station_data = stations.codeToStationData[station_code]
    lines = station_data['lineCodes']
    all_lines = station_data['allLines']
    all_codes = station_data['allCodes']
    station = Station.add(station_code,long_name, long_name, short_name, lines, all_lines, all_codes)
    print 'Added station: %s'%long_name



def write_units_json():
  """Write json files for each unit
  """
  from dcmetrometrics.common.JSONifier import JSONWriter
  import os
  jwriter = JSONWriter(basedir = os.path.join('client', 'app'))
  from dcmetrometrics.eles.models import Unit
  num_units = len(Unit.objects)
  for i, unit in enumerate(Unit.objects):
    print 'Writing unit %i of %i: %s'%(i, num_units, unit.unit_id)
    jwriter.write_unit(unit)

