"""
Utilities for creating logger objects.
"""
import logging, sys

BASE_NAME = 'dcmetrometrics'
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def abs_name(name):
  return "%s.%s"%(BASE_NAME, name)

def create_logger_with_handlers(name):

  # Get the logger
  logger = logging.getLogger(name)

  # Reset handlers on the logger. This is friendly
  # for debugging, so we avoid multiple handlres.
  logger.handlers = []

  # Create a stream handler
  sh = logging.StreamHandler(stream=sys.stderr)

  # create formatter
  formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

  # add formatter to stream handler
  sh.setFormatter(formatter)

  # add stream handler to logger
  logger.addHandler(sh)

  # set logging level
  logger.setLevel(logging.INFO)

  return logger

def get_logger(name):
  """Create a logger with no handlers. Handlers should 
  be attached to the root logger"""

  # Get the logger
  logger = logging.getLogger(name)
  return logger

create_logger = get_logger

def create_root_logger():

  # Get the logger
  logger = logging.getLogger()

  # Reset handlers on the logger. This is friendly
  # for debugging, so we avoid multiple handlres.
  logger.handlers = []

  # Create a stream handler to stderr
  sh = logging.StreamHandler(stream=sys.stderr)

  # add formatter to stream handler
  sh.setFormatter(formatter)

  # add stream handler to logger
  logger.addHandler(sh)

  # set logging level
  logger.setLevel(logging.INFO)

  return logger

def add_root_filehandler(fname):
  logger = logging.getLogger()
  fh = logging.FileHandler(fname)
  fh.setFormatter(formatter)
  logger.addHandler(fh)


