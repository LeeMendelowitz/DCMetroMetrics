"""
Script to compute the daily service reports for escalators and elevators.
This script will update the database and write json files for each updated day.
"""

##########################################
# Set up logging
from dcmetrometrics.common import logging_utils
logger = logging_utils.create_logger(__name__)
DEBUG = logger.debug
WARNING = logger.warning
INFO = logger.info

# Set up the ELES logger as well. This is used by other modules
logger_eles = logging_utils.create_logger("ELESApp")

##########################################

# Connect to the database
from dcmetrometrics.common import db_globals
db_globals.connect()

import sys, os
from datetime import datetime, date, timedelta
import gc
from operator import attrgetter
# gc.set_debug(gc.DEBUG_STATS)

from dcmetrometrics.common.db_globals import G
from dcmetrometrics.common.metro_times import getLastOpenTime
from dcmetrometrics.eles.models import Unit, SymptomCode, UnitStatus, SystemServiceReport
from datetime import timedelta
from dcmetrometrics.common.globals import WWW_DIR
from dcmetrometrics.common.utils import gen_days
from dcmetrometrics.common.jsonifier import JSONWriter




class ReturnObject(object):
  pass

def filter_consecutive_statuses(statuses):
  """
  Filter out consecutive statuses with the same symptom description
  """
  statuses = sorted(statuses, key = attrgetter('time'))
  last_status = None
  keep = []
  delete = []

  for s in statuses:

    if last_status is None:

      keep.append(s)

    else:

      if s.symptom_description != last_status.symptom_description:
        keep.append(s)
      else:
        delete.append(s)

    last_status = s

  ret = ReturnObject()
  ret.keep = keep
  ret.delete = delete
  return ret

def denormalize_unit_statuses():
  """
  Denormalized UnitStatus records by adding status and
  symptom fields to the UnitStatus.

  Also compute end_time and metro_open_time.
  """

  num_units = Unit.objects.no_cache().count()
  sys.stderr.write("Have %i units\n"%num_units)
  for i, unit in enumerate(Unit.objects.no_cache()):
    sys.stderr.write('Processing unit %s\n (%i of %i)'%(unit.unit_id, i, num_units))
    unit_statuses = UnitStatus.objects(unit = unit).no_cache().order_by('-time')
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

def fix_all_end_times_and_merge_consecutive():
  """
  Fix all end_time and metro_open_time.
  """

  num_units = Unit.objects.no_cache().count()
  sys.stderr.write("Have %i units\n"%num_units)

  GARBAGE_COLLECT_INTERVAL = 20

  for i, unit in enumerate(Unit.objects.no_cache()):

    INFO('Processing unit %s\n (%i of %i)'%(unit.unit_id, i, num_units))

    if i%GARBAGE_COLLECT_INTERVAL == 0:
      DEBUG("Running garbage collector after iteration over units.")
      count = gc.collect()
      DEBUG("Garbage collect returned %i"%count)

    unit_statuses = [s for s in UnitStatus.objects(unit = unit)]

    ret = filter_consecutive_statuses(unit_statuses)
    DEBUG("Have %i statuses for unit %s to delete"%(len(ret.delete), unit.unit_id))
    DEBUG("Have %i statuses for unit %s to keep"%(len(ret.keep), unit.unit_id))

    for s in ret.delete:
      DEBUG("Deleting unit status %s"%(s.pk))
      s.delete()

    del ret.delete

    unit_statuses = ret.keep
    unit_statuses = sorted(unit_statuses, key = attrgetter('time'), reverse = True)

    status_after = None

    for status in unit_statuses:

      if status_after:
        assert(status_after.symptom_description != status.symptom_description)
        status.end_time = status_after.time
        status.compute_metro_open_time()

      status.save()
      status_after = status

def compute_daily_service_reports(start_day = None, end_day = None, force_min_start_day = None):
  """
  Compute daily service reports for all units, and write json.
  """

  if not start_day:
    start_day = date(2013, 6, 1)

  if not end_day:
    end_day = date.today() # exclusive

  assert(end_day > start_day)

  num_units = Unit.objects.no_cache().count()
  sys.stderr.write("Have %i units\n"%num_units)

  GARBAGE_COLLECT_INTERVAL = 20

  min_start_day = start_day

  for i, unit in enumerate(Unit.objects.no_cache()):

    INFO('Computing daily service report unit %s\n (%i of %i)'%(unit.unit_id, i, num_units))

    if i%GARBAGE_COLLECT_INTERVAL == 0:
      DEBUG("Running garbage collector after iteration over units.")
      count = gc.collect()
      DEBUG("Garbage collect returned %i"%count)

    unit_statuses = sorted(unit.get_statuses(), key = attrgetter('time'), reverse = True)

    if not unit_statuses:
      continue

    last_status = unit_statuses[0]

    if start_day is not None:
      unit_start_day = min(start_day, getLastOpenTime(last_status.time).date())
    else:
      unit_start_day = getLastOpenTime(last_status.time).date()

    # Override the unit_start_day with force_min_start_day
    if force_min_start_day:
      unit_start_day = force_min_start_day

    unit.compute_daily_service_reports(start_day = unit_start_day, last_day = end_day,
      statuses = unit_statuses, save = True)

    min_start_day = min(min_start_day, unit_start_day)

  jwriter = JSONWriter(WWW_DIR)
  for day in gen_days(min_start_day, end_day):
    INFO('Computing system service report for day %s'%(day))
    report = SystemServiceReport.compute_for_day(day, save = True)
    jwriter.write_daily_system_service_report(report = report)



def recompute_performance_summaries():
  """Recompute performance summaries for all units"""
  from dcmetrometrics.eles.models import Unit
  units = Unit.objects.no_cache()
  start = datetime.now()
  n =  units.count()
  GARBAGE_COLLECT_INTERVAL = 10
  jwriter = JSONWriter(WWW_DIR)
  for i, unit in enumerate(units):

    INFO("Computing performance summary for unit %s: %i of %i (%.2f%%)"%(unit.unit_id, i, n, 100.0*i/n))
    unit.compute_performance_summary(save = True)

    if i%GARBAGE_COLLECT_INTERVAL == 0:
      DEBUG("Running garbage collector after iteration over units.")
      count = gc.collect()
      DEBUG("Garbage collect returned %i"%count)

    jwriter.write_unit(unit)
    
  # Write the station directory
  jwriter.write_station_directory()

  elapsed = (datetime.now() - start).total_seconds()
  print "%.2f seconds elapsed"%elapsed



def write_json():
  """Generate all json files.
  """
  from dcmetrometrics.common.jsonifier import JSONWriter
  import os

  jwriter = JSONWriter(WWW_DIR)
  # jwriter = JSONWriter(basedir = os.path.join('client', 'app'))

  from dcmetrometrics.eles.models import Unit
  num_units = Unit.objects.no_cache().count()
  for i, unit in enumerate(Unit.objects.no_cache()):
    logger.info('Writing unit %i of %i: %s'%(i, num_units, unit.unit_id))
    jwriter.write_unit(unit)

  # Write the station directory
  jwriter.write_station_directory()

  # Write the recent updates
  jwriter.write_recent_updates()  

  for report in SystemServiceReport.objects.no_cache():
    logger.info("Writing system service report for day %s"%report.day)
    jwriter.write_daily_system_service_report(report = report)


  elapsed = (datetime.now() - start).total_seconds()
  print "%.2f seconds elapsed"%elapsed

def fix_end_times():
  """
  Find units where the lastStatus has an end_time defined.

  This is a mysterious scenario and requires further investigation. Where do
  we set the end time on a status?

  If the last status has an end time defined, it will screw up the StatusGroup
  """
  from dcmetrometrics.eles.models import Unit

  to_fix = []
  key_statuses = (unit.key_statuses for unit in Unit.objects.no_cache())
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

def recompute_key_statuses():
  """Recompute key statuses for all units"""
  from dcmetrometrics.eles.models import Unit, KeyStatuses
  units = Unit.objects.no_cache()
  start = datetime.now()
  n = units.count()
  for i, unit in enumerate(units):
    print "Computing key statuses for unit %s: %i of %i (%.2f%%)"%(unit.unit_id, i, n, 100.0*i/n)
    unit.compute_key_statuses(save=True)
    
  elapsed = (datetime.now() - start).total_seconds()
  print "%.2f seconds elapsed"%elapsed

def run():
  recompute_key_statuses()
  fix_end_times()
  recompute_performance_summaries()

if __name__ == '__main__':
  run()
