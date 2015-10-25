"""
Script to compute the daily service reports for escalators and elevators.
This script will update the database and write json files for each updated day.
"""

# Connect to the database
from dcmetrometrics.common import db_globals
db_globals.connect()

import sys, os
from datetime import datetime, date, timedelta
import gc
from operator import attrgetter
# gc.set_debug(gc.DEBUG_STATS)

from dcmetrometrics.common.db_globals import G
from dcmetrometrics.eles import db_utils
from dcmetrometrics.common.metro_times import getLastOpenTime
from dcmetrometrics.eles.models import Unit, SymptomCode, UnitStatus, SystemServiceReport
from dcmetrometrics.common.globals import WWW_DIR
from dcmetrometrics.common.utils import gen_days
from dcmetrometrics.common.jsonifier import JSONWriter

import argparse
parser = argparse.ArgumentParser(description='Run daily service reports.')
parser.add_argument('--all', action = 'store_true',
                   help='Compute all, instead of a one day update.')


##########################################
# Set up logging
from dcmetrometrics.common import logging_utils
logger = logging_utils.create_logger(__name__)
DEBUG = logger.debug
WARNING = logger.warning
INFO = logger.info

# Set up the ELES logger as well. This is used by other modules
logger_eles = logging_utils.create_logger("ELESApp")
#########################################

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
   - start_day: The starting day for which to compute. This can be overridden by long running outages. 
      Computation will be unit dependent, depending on when its current outage goes back to.
   - end_day: The last day to compute, exclusive. By default this is today.
   - force_min_start_day: Force a minimum starting day for all computation. This overrides start_day or
     whatever the current outage suggest to do.
  """

  if not start_day:
    start_day = date(2013, 6, 1)

  if not end_day:
    end_day = date.today() # exclusive

  assert(end_day > start_day)

  num_units = Unit.objects.no_cache().count()
  sys.stderr.write("Have %i units\n"%num_units)

  GARBAGE_COLLECT_INTERVAL = 20

  min_start_day = force_min_start_day if force_min_start_day else start_day

  # This long loop was raising Exceptions like:
  # pymongo.errors.OperationFailure: cursor id 'XXXX' not valid at server
  # Solution is to not timeout the cursor and explicitly close it ourselves
  units = Unit.objects.timeout(False).no_cache()

  for i, unit in enumerate(units):

    INFO('Computing daily service report unit %s\n (%i of %i)'%(unit.unit_id, i, num_units))

    if i%GARBAGE_COLLECT_INTERVAL == 0:
      DEBUG("Running garbage collector after iteration over units.")
      count = gc.collect()
      DEBUG("Garbage collect returned %i"%count)

    unit_statuses = sorted(unit.get_statuses(), key = attrgetter('time'), reverse = True)

    if not unit_statuses:
      continue

    last_status = unit_statuses[0]

    # If the last status is non-operational, consider making updates back to
    # the start of the outage.
    unit_start_day = start_day
    if last_status.symptom_category != "ON":
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

  if force_min_start_day:
    min_start_day = force_min_start_day

  # We are done with the units query set, so close the cursor.
  units._cursor.close()


  jwriter = JSONWriter(WWW_DIR)
  for day in gen_days(min_start_day, end_day):
    INFO('Computing system service report for day %s'%(day))
    report = SystemServiceReport.compute_for_day(day, save = True)
    jwriter.write_daily_system_service_report(report = report)



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

def run_all():
  start_day = date(2013, 6, 1)
  end_day = date.today() - timedelta(days = 1)

  compute_daily_service_reports(
    start_day = start_day,
    end_day = end_day,
    force_min_start_day = start_day)

def run_update():
  start_day = date.today() - timedelta(days = 1)
  end_day = date.today()

  compute_daily_service_reports(
    start_day = start_day,
    end_day = end_day)

if __name__ == '__main__':
  args = parser.parse_args()
  start_time = datetime.now()
  if args.all:
    logger.info("Running all.")
    run_all()
  else:
    logger.info("Running one day update.")
    run_update()
  end_time = datetime.now()
  run_time = (end_time - start_time).total_seconds()
  logger.info("%.2f seconds elapsed"%run_time)