"""
Script to export data as csv to share on the world wide web.
"""

# Connect to the database
from dcmetrometrics.common import dbGlobals
dbGlobals.connect()

import sys, os
from datetime import datetime, date, timedelta
from operator import attrgetter
# gc.set_debug(gc.DEBUG_STATS)

from dcmetrometrics.eles.models import Unit, SymptomCode, UnitStatus, SystemServiceReport
from dcmetrometrics.common.globals import WWW_DIR
from dcmetrometrics.common.DataWriter import DataWriter

import argparse
parser = argparse.ArgumentParser(description='Export CSV data.')


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


def run():

  dwriter = DataWriter(WWW_DIR)

  logger.info("Writing units...")
  dwriter.write_units()
  logger.info("done.")

  logger.info("Writing unit statuses...")
  dwriter.write_unit_statuses()
  logger.info("done.")

  logger.info("Writing hotcars...")
  dwriter.write_hot_cars()
  logger.info("done.")


if __name__ == '__main__':

  args = parser.parse_args()

  start_time = datetime.now()
  run()
  end_time = datetime.now()

  run_time = (end_time - start_time).total_seconds()
  logger.info("%.2f seconds elapsed"%run_time)