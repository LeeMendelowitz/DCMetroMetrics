# Script to migrate from mongoexport json dump 
# to SQL models

from dcmetrometrics.eles import sql_models
from dcmetrometrics.eles.sql_models import Station, StationGroup
from dcmetrometrics.common.db_utils import get_dcmm_db
from dcmetrometrics.common import logging_utils

logger = logging_utils.get_logger(__name__)
db_manager = get_dcmm_db()
engine = db_manager.engine

import json


sql_models.Base.metadata.create_all(engine) 

def migrate_stations(station_json):
  """
  Load stations from json and rebuild the entire
  station and station_group table
  """

  station_data = []

  with open(station_json) as f:
    for l in f:
      data = l.strip()
      if data:
        station_data.append(json.loads(data))

  logger.info("Dropping and creating the station and station group tables")

  Station.__table__.drop(engine, checkfirst = True)
  StationGroup.__table__.drop(engine, checkfirst = True)
  sql_models.Base.metadata.create_all(engine) 

  session = db_manager.session

  line_code_to_attr = [
    ('RD', 'red'),
    ('OR', 'orange'),
    ('YL', 'yellow'),
    ('GR', 'green'),
    ('BL', 'blue'),
    ('SV', 'silver')
  ]

  station_name_to_group = {}
  station_code_to_obj = {}
  station_objs = []

  for s in station_data:

    station_obj = Station(code = s['_id'])
    station_group = station_name_to_group.get(s['short_name'], None)

    if station_group is None:
      station_group = StationGroup(
          short_name = s['short_name'],
          medium_name = s['medium_name'],
          long_name = s['long_name'])
      station_name_to_group[station_group.short_name] = station_group

    lines = set(s['lines'])

    # Set the red/orange/yellow/green/blue/silver attributes
    for line_code, attr in line_code_to_attr:
      setattr(station_obj, attr, line_code in lines)

    station_objs.append(station_obj)

  logger.info("Created %i station objects"%(len(station_objs)))
  logger.info("Created %i station groups"%(len(station_name_to_group)))

  # Create the station groups
  for name, station_group in station_name_to_group.iteritems():
    session.add(station_group)

  session.commit()

if __name__ == '__main__':

  logger = logging_utils.create_root_logger()
  station_json = '/data/repo_dev/mongoexport/stations.json'
  migrate_stations(station_json)
