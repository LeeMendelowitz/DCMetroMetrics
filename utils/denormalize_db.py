"""
Script to denormalize the database by adding fields to the unit status records.

This should be imported as a module and not run directly.
"""

from . import utils
utils.fixSysPath()

import sys
from datetime import datetime

from dcmetrometrics.common.dbGlobals import G
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
  Create station documents from the stations.py module.
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


def update_symptom_codes():
  """
  Update symptom codes from the old format to the new format.
   - Key difference: Do not use symptom code as a primary key anymore, since the codes have been deprected
  """

  from dcmetrometrics.eles import models, defs
  from mongoengine.context_managers import switch_db, switch_collection

  # Fish out symptom codes in the old format from the symptom_code collection
  # Backup to the symptom_code_old collection
  with switch_collection(models.SymptomCodeOld, "symptom_codes") as SymptomCodeOld:
    old_symptoms = list(models.SymptomCodeOld.objects)
    for s in old_symptoms:
      # Make a backup of the old symptom codes
      s.switch_collection('symptom_codes_old')
      s.save() # Save to the new collection

  # Remove the symptom collection - out with the old, in with the new!
  models.SymptomCode.drop_collection() # Clears the "symptom_code" collection

  with switch_collection(models.SymptomCodeOld, "symptom_codes_old") as SymptomCodeOld:
    s_old = list(SymptomCodeOld.objects)
    for s in s_old:
      s_new = s.make_new_format()
      if not s_new.category:
        s_new.category = defs.symptomToCategory[s_new.description]
      print "saving: ", s_new
      s_new.save()

def update_symptom_code_category():
  """Update the symptom categories"""
  from dcmetrometrics.eles import models, defs
  for s in SymptomCode.objects:
    category = defs.symptomToCategory[s.description]
    s.category = category
    s.save()

def update_unit_statuses():
  """
  Update unit statuses to reference the new symptom collection
  """

  from dcmetrometrics.eles import models
  from mongoengine.context_managers import switch_db, switch_collection

  d2r = dict() # Symptom description to record
  for s in models.SymptomCode.objects:
    d2r[s.description] = s


  # Fish out UnitStatus in the old format from the symptom_code collection
  # Backup to the symptom_code_old collection
  print """Exporting from collection escalator_statuses, assuming records are in the old format.
If successful, will backup to collection escalator_statuses_old..."""
  try:
    with switch_collection(models.UnitStatusOld, "escalator_statuses") as UnitStatusOld:
      n = len(models.UnitStatusOld.objects)
      for i, s in enumerate(models.UnitStatusOld.objects):
        # Make a backup of the old unit statuses
        print "Backing up unit status %i of %i (%.2f %%)"%(i, n, float(i)/n*100.0)
        s.switch_collection('escalator_statuses_old')
        s.save() # Save to the new collection
  except Exception as e:
    print "Caught Exception!\n"
    print str(e)
    return

  # Save unit statuses in the new format.
  n = len(models.UnitStatusOld.objects)
  for i, s_old in enumerate(models.UnitStatusOld.objects):
    print 'Reformatting unit status %i of %i (%.2f %%)'%(i, n, float(i)/n*100.0)
    s_new = s_old.to_new_format()
    s_new.pk = s_old.pk
    s_new.symptom = d2r[s_old.symptom.description]
    s_new.save()


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

def delete_recent_statuses():
  """Delete statuses from the past two days.
  Recompute keystatuses for affected units"""
  from dcmetrometrics.common import metroTimes
  from datetime import timedelta
  from dcmetrometrics.eles.models import UnitStatus
  t0 = metroTimes.utcnow() - timedelta(days = 2)
  statuses = UnitStatus.objects(time__gt = t0)
  units = set(s.unit for s in statuses)
  print "Deleting %i recent statuses"%len(statuses)
  for s in statuses:
    s.delete()

  for u in units:
    print "computing key statuses for unit: %s"%u.unit_id
    u.compute_key_statuses()

def recompute_key_statuses():
  """Recompute key statuses for all units"""
  from dcmetrometrics.eles.models import Unit, KeyStatuses
  units = Unit.objects
  start = datetime.now()
  n = len(units)
  KeyStatuses.drop_collection()
  for i, unit in enumerate(Unit.objects):
    print "Computing key statuses for unit %s: %i of %i (%.2f%%)"%(unit.unit_id, i, n, 100.0*i/n)
    unit.compute_key_statuses()

  elapsed = (datetime.now() - start).total_seconds()
  print "%.2f seconds elapsed"%elapsed

def delete_units_missing_statuses():
  """Delete units with no statuses"""
  from dcmetrometrics.eles.models import Unit
  units = Unit.objects
  start = datetime.now()
  n = len(units)
  for i, unit in enumerate(Unit.objects):
    print "Checking unit %s: %i of %i (%.2f%%)"%(unit.unit_id, i, n, 100.0*i/n)
    statuses = unit.get_statuses()
    if len(statuses) == 0:
      # Delete the unit, delete key statuses
      print "Deleting unit %s"%unit.unit_id
      ks = unit.get_key_statuses()
      ks.delete()
      unit.delete()

  elapsed = (datetime.now() - start).total_seconds()
  print "%.2f seconds elapsed"%elapsed

def bad_key_statuses():
  """Return key statuses where we can't dereference the unit"""
  from dcmetrometrics.eles.models import KeyStatuses
  ks = KeyStatuses.objects.select_related()
  bad = []
  for k in ks:
    try:
      print k.unit.unit_id
    except Exception as e:
      bad.append(k)
  return bad
  