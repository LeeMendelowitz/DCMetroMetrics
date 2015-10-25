"""
Script to export data as csv to share on the world wide web.
"""

# Connect to the database
from dcmetrometrics.common import db_globals
dbGlobals.connect()

import sys, os
from datetime import datetime, date, timedelta
from operator import attrgetter
import shutil
# gc.set_debug(gc.DEBUG_STATS)

from dcmetrometrics.eles.models import Unit, SymptomCode, UnitStatus, SystemServiceReport
from dcmetrometrics.common.globals import (WWW_DIR, REPO_DIR)
from dcmetrometrics.common.data_writer import DataWriter

import argparse
parser = argparse.ArgumentParser(description='Export CSV data.')
parser.add_argument('--no-write', action = 'store_true',
                   help='Do not write database .csv files - use existing instead.')


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


def run(no_write = False):

  dwriter = DataWriter(WWW_DIR)
  OUT_DIR = dwriter.outdir

  if not no_write:

    logger.info("Writing units...")
    dwriter.write_units()
    logger.info("done.")

    logger.info("Writing unit statuses...")
    dwriter.write_unit_statuses()
    logger.info("done.")

    logger.info("Writing hotcars...")
    dwriter.write_hot_cars()
    logger.info("done.")

    logger.info("Writing stations...")
    dwriter.write_stations()
    logger.info("done")

    logger.info("Writing daily system report...")
    dwriter.write_system_daily_service_report()
    logger.info("done")

    logger.info("Writing daily unit report...")
    dwriter.write_unit_daily_service_report()
    logger.info("done")

  # Write a timestamp
  dwriter.write_timestamp()

  # Copy the readme
  readme = os.path.join(REPO_DIR, 'data', 'data_readme.md')
  readme_target = os.path.join(OUT_DIR, 'README.md')
  shutil.copy(readme, readme_target)

  # Copy the license
  license = os.path.join(REPO_DIR, 'data', 'odbl-10.txt')
  shutil.copy(license, os.path.join(OUT_DIR, "LICENSE"))

  # If the zip file already exists in the tree, delete it
  zip_file = os.path.join(OUT_DIR, 'dcmetrometrics.zip')
  if os.path.exists(zip_file):
    logger.info('Deleting existing zip file: %s', zip_file)
    os.unlink(zip_file)

  # Now copy the tree
  logger.info("copying output directory...")
  tree_to_zip = os.path.join(OUT_DIR, 'dcmetrometrics')
  shutil.rmtree(tree_to_zip, ignore_errors = True)
  shutil.copytree(OUT_DIR, tree_to_zip)

  # zip the copied tree
  logger.info("making archive...")
  output_file = shutil.make_archive('dcmetrometrics', 'zip', root_dir = dwriter.outdir,
    base_dir = 'dcmetrometrics')

  logger.info('writing to %s', zip_file)
  shutil.move(output_file, zip_file)

  # delete the copied tree
  logger.info('cleaning up...')
  shutil.rmtree(tree_to_zip)


if __name__ == '__main__':

  args = parser.parse_args()

  start_time = datetime.now()
  run(args.no_write)
  end_time = datetime.now()

  run_time = (end_time - start_time).total_seconds()
  logger.info("%.2f seconds elapsed"%run_time)