# Script to migrate from mongoexport json dump 
# to SQL models

from dcmetrometrics.eles import sql_models
from dcmetrometrics.eles.sql_models import \
  (Station, StationGroup, Unit, UnitStatus, SymptomCode)

from dcmetrometrics.common.db_utils import get_dcmm_db
from dcmetrometrics.common import logging_utils

logger = logging_utils.get_logger(__name__)
db_manager = get_dcmm_db()
engine = db_manager.engine
session = db_manager.session
import json

sql_models.Base.metadata.create_all(engine) 

# def migrate_stations(station_json):
#   """
#   Load stations from json and rebuild the entire
#   station and station_group table
#   """

#   station_data = []

#   with open(station_json) as f:
#     for l in f:
#       data = l.strip()
#       if data:
#         station_data.append(json.loads(data))

#   logger.info("Dropping and creating the station and station group tables")

#   Station.__table__.drop(engine, checkfirst = True)
#   StationGroup.__table__.drop(engine, checkfirst = True)

#   line_code_to_attr = [
#     ('RD', 'red'),
#     ('OR', 'orange'),
#     ('YL', 'yellow'),
#     ('GR', 'green'),
#     ('BL', 'blue'),
#     ('SV', 'silver')
#   ]

#   station_name_to_group = {}
#   station_code_to_obj = {}
#   station_objs = []

#   for s in station_data:

#     station_obj = Station(code = s['_id'])
#     station_group = station_name_to_group.get(s['short_name'], None)

#     if station_group is None:
#       station_group = StationGroup(
#           short_name = s['short_name'],
#           medium_name = s['medium_name'],
#           long_name = s['long_name'])
#       station_name_to_group[station_group.short_name] = station_group

#     lines = set(s['lines'])

#     # Set the red/orange/yellow/green/blue/silver attributes
#     for line_code, attr in line_code_to_attr:
#       setattr(station_obj, attr, line_code in lines)

#     station_objs.append(station_obj)

#   logger.info("Created %i station objects"%(len(station_objs)))
#   logger.info("Created %i station groups"%(len(station_name_to_group)))

#   # Create the station groups
#   for name, station_group in station_name_to_group.iteritems():
#     session.add(station_group)

#   # Create the stations
#   for station in station_objs:
#     session.add(station)

#   session.commit()

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

  engine.execute(Station.__table__.delete())
  engine.execute(StationGroup.__table__.delete())
  
  sql_models.Base.metadata.create_all(engine)

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

    station_obj.station_group = station_group

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

  for station in station_objs:
    session.add(station)

  session.commit()


def migrate_units(units_json):
  """
  Load units from json and rebuild the entire
  units table. This will erase the UnitStatus table.
  """

  recs = []


  with open(units_json) as f:
    for l in f:
      data = l.strip()
      if data:
        recs.append(json.loads(data))

  logger.info("Dropping and creating the unit_status and unit tables")

  engine.execute(UnitStatus.__table__.delete())
  engine.execute(Unit.__table__.delete())

  

  for rec in recs:
    symptom = SymptomCode()
    session.add(unit)

  logger.info("Adding %i units"%len(recs))
  
  session.commit()

def migrate_symptoms(symptoms_json):
  """
  Load symptoms from json. This will delete the entries in the
  UnitStatus table due to foreign key constraints.
  """

  recs = []

  with open(symptoms_json) as f:
    for l in f:
      data = l.strip()
      if data:
        recs.append(json.loads(data))

  logger.info("Dropping and creating the symptom tables")
  engine.execute(UnitStatus.__table__.delete())
  engine.execute(SymptomCode.__table__.delete())

  # Make symptom descriptions upper case
  seen = set()
  urecs = []
  for rec in recs:
    rec['symptom_desc'] = rec['symptom_desc'].upper()
    if rec['symptom_desc'] in seen:
      continue
    seen.add(rec['symptom_desc'])
    urecs.append(rec)

  symptoms = []
  for rec in urecs:
    symptom = SymptomCode(
      description = rec['symptom_desc'],
      category = rec['category']
    )
    symptoms.append(symptom)
    session.add(symptom)


  logger.info("Adding %i symptoms"%len(recs))
  
  session.commit()

if __name__ == '__main__':

  logger = logging_utils.create_root_logger()

  station_json = '/data/repo_dev/mongoexport/stations.json'
  migrate_stations(station_json)

  symptom_json = '/data/repo_dev/mongoexport/symptom_codes.json'
  migrate_symptoms(symptom_json)

  unit_json = '/data/repo_dev/mongoexport/escalators.json'
  migrate_units(unit_json)
