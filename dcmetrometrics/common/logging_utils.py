"""
Utilities for creating logger objects.
"""
import logging, sys


def create_logger(name):

  # Get the logger
  logger = logging.getLogger(name)

  # Reset handlers on the logger.
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
  logger.setLevel(logging.DEBUG)

  return logger