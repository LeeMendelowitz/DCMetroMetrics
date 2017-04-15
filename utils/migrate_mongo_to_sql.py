# Script to migrate from mongoexport json dump 
# to SQL models
import utils
utils.fixSysPath()

from dcmetrometrics.eles import sql_models
from dcmetrometrics.eles.sql_models import \
  (Station, StationGroup, Unit, UnitStatus, Symptom)

import dcmetrometrics.hotcars.sql_models as hotcar_sql_models
from dcmetrometrics.hotcars.sql_models import \
  (Temperature, HotCarTweet, HotCarTweeter, HotCarReport)

from dcmetrometrics.common.db_utils import get_dcmm_db
from dcmetrometrics.common import logging_utils
from datetime import datetime, date

logger = logging_utils.get_logger(__name__)
db_manager = get_dcmm_db()
engine = db_manager.engine
session = db_manager.session
import json, re, dateutil.parser

sql_models.Base.metadata.create_all(engine)
hotcar_sql_models.Base.metadata.create_all(engine)

############################################

def clean_text(s):
  """Remove punctuation from text"""
  return re.sub('[^0-9a-zA-Z]', '', s)

def safe_get(d, k):
  if d is None:
    return d
  v = d.get(k, None)
  return v

def safe_parse_time(v):

  if v is None:
    return None

  return dateutil.parser.parse(v)

def get_time_field(rec, k):
  return safe_parse_time(safe_get(safe_get(rec, k), '$date'))

def get_int_field(rec, k):

  v = rec.get(k, None)

  if isinstance(v, dict) and '$numberLong' in v:
    return safe_int(v['$numberLong'])

  return safe_int(v)

def get_utf8(rec, k):
  v = rec.get(k, None)
  if v:
    v = v.encode('utf-8')
  return v

def safe_int(v):
  if v is None:
    return None
  try:
    return int(v)
  except Exception:
    return None

def yield_recs(fname):

  with open(fname) as f:

    for i, l in enumerate(f):

      try:
        rec = json.loads(l)
        yield rec

      except Exception as e:
        logger.warning("error parsing line %i of file %s:%s\n%s"%(i, fname, str(e), l))



##########################################

def reset_database():

  # Drop all tables
  classes = [UnitStatus, Unit, Station, StationGroup]

  for cl in classes:
    logger.info("Dropping table %s"%cl.__name__)
    cl.__table__.drop(engine, checkfirst=True)

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

  reset_database()

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
          short_name = clean_text(s['short_name']),
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

  num_added = 0

  for rec in recs:

    unit = Unit(
      id = rec['unit_id'],
      station_code = rec['station_code'],
      unit_desc = rec['esc_desc'],
      unit_type = rec['unit_type']
    )

    try:

      session.add(unit)
      session.commit()
      logger.info("Added %s."%unit.id)
      num_added += 1

    except Exception as e:
      logger.error("Caught exception when adding unit %s: %s"%(rec['unit_id'], e))
      session.rollback()
  

  logger.info("Added %i units."%num_added)

  session.commit()


def migrate_unit_statuses(unit_statuses_json):

  engine.execute(UnitStatus.__table__.delete())

  num_added = 0

  # load units and symptoms for lookup
  symptoms = session.query(Symptom).all()
  symptom_lookup = {s.description:s for s in symptoms}

  units = session.query(Unit).all()
  unit_lookup = {u.id:u for u in units}

  def process_record(rec):

      unit = unit_lookup[rec['unit_id']]
      symptom = symptom_lookup[rec['symptom_description'].upper()]

      unit_status = UnitStatus(
        unit = unit,
        symptom = symptom,
        time = get_time_field(rec, 'time'),
        end_time = get_time_field(rec, 'end_time'),
        metro_open_time = rec.get('metro_open_time', None),
        tick_delta = rec['tickDelta'],
        update_type = rec.get('update_type', None)
      )

      return unit_status

  with open(unit_statuses_json) as f:

    for l in f:

      try:

        data = l.strip()
        rec = json.loads(data)

        status = process_record(rec)
        session.add(status)
        session.commit()

        num_added += 1

        logger.info("Added %i statuses"%num_added)

      except Exception as e:

        session.rollback()
        logger.error("Error while processing record: %s\n\n%s"%(str(e), l))

  logger.info("Finished processing %i statuses"%num_added)


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
  engine.execute(Symptom.__table__.delete())

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
    symptom = Symptom(
      description = rec['symptom_desc'],
      category = rec['category']
    )
    symptoms.append(symptom)
    session.add(symptom)


  logger.info("Adding %i symptoms"%len(recs))
  
  session.commit()

def migrate_temperatures(temperature_json):
  """
  Load symptoms from json. This will delete the entries in the
  UnitStatus table due to foreign key constraints.
  """
  recs = yield_recs(temperature_json)

  logger.info("Dropping and creating the temperatures tables")

  engine.execute(Temperature.__table__.delete())

  num_added = 0

  for rec in recs:

    temp = Temperature(
      date = get_time_field(rec, "_id"),
      max_temp = rec.get('maxTemp', None)
    )

    try:

      session.add(temp)
      session.commit()

      num_added += 1

    except Exception as e:

      session.rollback()
      logger.error("Caught exception while processing record: %s\n%s"%(str(e), rec))

  logger.info("Adding %i temperatures"%num_added)
  session.commit()

def migrate_hotcar_tweets(json_file):
  """
  Load symptoms from json. This will delete the entries in the
  UnitStatus table due to foreign key constraints.
  """
  recs = yield_recs(json_file)

  logger.info("Dropping and creating the hotcar_tweets tables")

  engine.execute(HotCarTweet.__table__.delete())

  num_added = 0

  for rec in recs:

    hot_car_tweet = HotCarTweet(
      tweet_id = get_int_field(rec, '_id'),
      ack = rec['ack'],
      embed_html = get_utf8(rec, 'embed_html'),
      text = get_utf8(rec, 'text'),
      time = get_time_field(rec, 'time'),
      user_id = get_int_field(rec, 'user_id')
    )

    try:

      session.add(hot_car_tweet)
      session.commit()

      num_added += 1  

    except Exception as e:

      session.rollback()
      logger.error("Caught exception while processing record: %s\n%s"%(str(e), rec))

  logger.info("Adding %i hot_car_tweets"%num_added)
  session.commit()


def migrate_hot_car_reports(json_file):
  """
  Load reports from the hot car reports json file
  """
  recs = yield_recs(json_file)

  logger.info("Dropping and creating the hot_car_reports tables")

  engine.execute(HotCarReport.__table__.delete())

  num_added = 0

  for rec in recs:

    hot_car_report = HotCarReport(
      
      tweet_pk = get_int_field(rec, 'tweet_id'),
      color = get_utf8(rec, 'color'),
      car_number = get_int_field(rec, 'car_number') 

    )

    try:

      session.add(hot_car_report)
      session.commit()

      num_added += 1  

    except Exception as e:

      session.rollback()
      logger.error("Caught exception while processing record: %s\n%s"%(str(e), rec))

  logger.info("Adding %i hot_car_reports"%num_added)
  session.commit()

def migrate_hotcar_tweeters(json_file):

  recs = yield_recs(json_file)

  logger.info("Dropping and creating the hotcar_tweeters tables")

  engine.execute(HotCarTweeter.__table__.delete())

  num_added = 0

  for rec in recs:

    row = HotCarTweeter(
      user_id = get_int_field(rec, 'user_id'),
      handle = get_utf8(rec, 'handle')
    )

    try:

      session.add(row)
      session.commit()

      num_added += 1  

    except Exception as e:

      session.rollback()
      logger.error("Caught exception while processing record: %s\n%s"%(str(e), rec))

  logger.info("Adding %i hot_car_tweeters"%num_added)
  session.commit()

if __name__ == '__main__':

  logger = logging_utils.create_root_logger()

  date_str = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
  fname = 'migration.%s.log'%(date_str)
  logging_utils.add_root_filehandler(fname)

  station_json = '/data/repo_dev/mongoexport/stations.json'
  migrate_stations(station_json)

  symptom_json = '/data/repo_dev/mongoexport/symptom_codes.json'
  migrate_symptoms(symptom_json)

  unit_json = '/data/repo_dev/mongoexport/escalators.json'
  migrate_units(unit_json)

  unit_statuses_json = '/data/repo_dev/mongoexport/escalator_statuses.json'
  migrate_unit_statuses(unit_statuses_json)

  temperatures_json = '/data/repo_dev/mongoexport/temperatures.json'
  migrate_temperatures(temperatures_json)

  hot_car_tweeter_json = '/data/repo_dev/mongoexport/hotcars_tweeters.json'
  migrate_hotcar_tweeters(hot_car_tweeter_json)

  hot_car_tweet_json = '/data/repo_dev/mongoexport/hotcars_tweets.json'
  migrate_hotcar_tweets(hot_car_tweet_json)
  
  hot_car_report_json = '/data/repo_dev/mongoexport/hotcars.json'
  migrate_hot_car_reports(hot_car_report_json)
