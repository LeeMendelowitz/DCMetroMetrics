"""
Script to perform database migrations for the ELES App.

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
from datetime import timedelta


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
  for i,s in enumerate(SymptomCode.objects):
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
      n = models.UnitStatusOld.objects.count()
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
  n = models.UnitStatusOld.objects.count()
  for i, s_old in enumerate(models.UnitStatusOld.objects):
    print 'Reformatting unit status %i of %i (%.2f %%)'%(i, n, float(i)/n*100.0)
    s_new = s_old.to_new_format()
    s_new.pk = s_old.pk
    s_new.symptom = d2r[s_old.symptom.description]
    s_new.save()


def write_json():
  """Generate all json files.
  """
  from dcmetrometrics.common.JSONifier import JSONWriter
  import os

  jwriter = JSONWriter(basedir = os.path.join('client', 'app'))

  from dcmetrometrics.eles.models import Unit
  num_units = Unit.objects.count()
  for i, unit in enumerate(Unit.objects):
    print 'Writing unit %i of %i: %s'%(i, num_units, unit.unit_id)
    jwriter.write_unit(unit)

  # Write the station directory
  jwriter.write_station_directory()

  # Write the recent updates
  jwriter.write_recent_updates()  



def delete_recent_statuses(time_delta = timedelta(hours = 2)):
  """Delete statuses from the past two days.
  Recompute keystatuses for affected units"""
  from dcmetrometrics.common import metroTimes

  from dcmetrometrics.eles.models import UnitStatus
  t0 = metroTimes.utcnow() - time_delta
  statuses = UnitStatus.objects(time__gt = t0)
  units = set(s.unit for s in statuses)
  print "Deleting %i recent statuses"%len(statuses)
  for s in statuses:
    s.delete()

  for u in units:
    print "computing key statuses for unit: %s"%u.unit_id
    u.compute_key_statuses()

def delete_last_n_statuses(n):
  """Delete the last n statuses"""
  from dcmetrometrics.common import metroTimes

  from dcmetrometrics.eles.models import UnitStatus

  statuses = UnitStatus.objects().order_by('-time').limit(n)
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
  for i, unit in enumerate(Unit.objects):
    print "Computing key statuses for unit %s: %i of %i (%.2f%%)"%(unit.unit_id, i, n, 100.0*i/n)
    unit.compute_key_statuses()
    
  elapsed = (datetime.now() - start).total_seconds()
  print "%.2f seconds elapsed"%elapsed

def recompute_performance_summaries():
  """Recompute performance sumamries for all units"""
  from dcmetrometrics.eles.models import Unit
  units = Unit.objects
  start = datetime.now()
  n = len(units)

  for i, unit in enumerate(Unit.objects):
    print "Computing performance summary for unit %s: %i of %i (%.2f%%)"%(unit.unit_id, i, n, 100.0*i/n)
    unit.compute_performance_summary()
    
  elapsed = (datetime.now() - start).total_seconds()
  print "%.2f seconds elapsed"%elapsed

def delete_units_missing_statuses():
  """Delete units with no statuses"""
  from dcmetrometrics.eles.models import Unit
  units = Unit.objects
  start = datetime.now()
  n = len(units)
  report_interval = max(int(n/100 + 0.5), 1)
  report_counter = 0
  for i, unit in enumerate(Unit.objects):
    report_counter += 1
    if report_counter == report_interval:
      sys.stdout.write(".")
      sys.stdout.flush()
      report_counter = 0

   # print "Checking unit %s: %i of %i (%.2f%%)"%(unit.unit_id, i, n, 100.0*i/n)
    statuses = unit.get_statuses()
    if len(statuses) == 0:
      # Delete the unit, delete key statuses
      print "Deleting unit %s"%unit.unit_id
      ks = unit.get_key_statuses()
      ks.delete()
      unit.delete()

  elapsed = (datetime.now() - start).total_seconds()
  sys.stdout.write("\n%.2f seconds elapsed\n"%elapsed)

def bad_key_statuses():
  """Return key statuses where we can't dereference the unit"""
  from dcmetrometrics.eles.models import KeyStatuses
  ks = KeyStatuses.objects.select_related()
  bad = []


  for k in ks:
    try:
      a = k.unit.unit_id
    except Exception as e:
      bad.append(k)
  return bad


def add_status_update_type():
  """Fill in the update field for all statuses"""
  from dcmetrometrics.eles.models import Unit, KeyStatuses
  units = Unit.objects
  start = datetime.now()
  n = len(units)
  for i, unit in enumerate(units):
    print "Updating status types for unit %s: %i of %i (%.2f%%)"%(unit.unit_id, i, n, 100.0*i/n)
    statuses = unit.get_statuses()[::-1] # Sort in ascending order of time
    was_broken = False
    was_off = False
    is_first = True
    it = iter(statuses)
    for s in statuses:

      if is_first:
        s.update_type = 'Update'
        s.save()
        is_first = False
        continue

      # Handle now on case
      if s.symptom_category == 'ON':
        if was_broken:
          s.update_type = 'Fix'
        else:
          s.update_type = 'On'
        was_broken = False
        was_off = False

      # Handle now broken case
      elif s.symptom_category == 'BROKEN':

        if was_broken:
          s.update_type = 'Update'
        else:
          s.update_type = 'Break'

        was_off = True
        was_broken = True

      # Handle now off for other reason case
      else:

        if not was_off:
          s.update_type = 'Off'
        else:
          s.update_type = 'Update'

        was_off = True

      s.save()

  elapsed = (datetime.now() - start).total_seconds()
  print "%.2f seconds elapsed"%elapsed

def update_2014_08_24():

  # First, update the status classifications using the latest defs.
  print "Updating symptom code categories."
  update_symptom_code_category()

  # Now denormalize all the unit statuses to bring them up to date.
  print "Denormalizing unit statuses."
  denormalize_unit_statuses()

  print "Adding status update types."
  add_status_update_type()

  print "Generating all JSON"
  write_json()


def update_2014_08_25():
    # If a hot car has a color of NONE, set to None.
    from dcmetrometrics.hotcars.models import HotCarReport
    count = 0
    for hc in HotCarReport.objects(color = "NONE"):
      count += 1
      hc.color = None
      hc.save()
    print "Reset color on %i records"%count


def fix_end_times():
  """
  Find units where the lastStatus has an end_time defined.

  This is a mysterious scenario and requires further investigation. Where do
  we set the end time on a status?
  """
  from dcmetrometrics.eles.models import Unit

  to_fix = []
  key_statuses = (unit.key_statuses for unit in Unit.objects)
  for ks in key_statuses:
    if ks.lastStatus.end_time is not None:
      to_fix.append(ks)

  print "have %i units with lastStatus with defined end_time"%len(to_fix)
  print [ks.unit_id for ks in to_fix]

  for ks in to_fix:
    lastStatus = ks.lastStatus
    lastStatus.end_time = None
    lastStatus.clean()
    lastStatus.save()


def update_2014_09_10():
  recompute_key_statuses()
  fix_end_times()
  recompute_performance_summaries()
  write_json()

  