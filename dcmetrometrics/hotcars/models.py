"""
Models for HotCars app.
"""

from mongoengine import *
from ..common.WebJSONMixin import WebJSONMixin
from ..common.metroTimes import utcnow, tzutc

from datetime import timedelta, datetime, date
from collections import defaultdict

class HotCarAppState(Document):

  id = IntField(required=True, default = 1, db_field = '_id', primary_key=True)
  lastMentionsCheckTime = DateTimeField()
  lastMentionsTweetId = LongField()
  lastRunTime = DateTimeField()
  lastSelfTweetId = LongField()
  lastTweetId = LongField()

  meta = {'collection' : 'hotcars_appstate'}

  @classmethod
  def update_run_time(cls, runTime):
    try:
      doc = cls.objects(pk = 1).get()
    except DoesNotExist:
      doc = cls(id  = 1, lastRunTime = runTime)

    doc.lastRunTime = runTime
    doc.save()

  @classmethod
  def update(cls, **kwargs):
    """
    Update the app state entry
    """
    try:
      doc = cls.objects(pk = 1).get()
    except DoesNotExist:
      doc = cls(id  = 1)

    # Add the attributes, and save the document
    for k, v in kwargs.iteritems():
      setattr(doc, k, v)

    doc.save()

  @classmethod
  def get(cls):
    return cls.objects.get(pk = 1)



class HotCarTweeter(WebJSONMixin, Document):
  """Information on a Hot Car Tweeter"""
  user_id = LongField(primary_key = True, required=True, db_field='_id')
  handle = StringField(required = True)

  meta = {'collection' : 'hotcars_tweeters'}
  web_json_fields = ['id', 'handle']

  @classmethod
  def update(cls, user_id, handle):

    doc = None
    try:
      doc = cls.objects(user_id = user_id).get() 
    except DoesNotExist:
      doc = cls(user_id = user_id)

    doc.handle = handle;
    doc.save()
    return doc


class HotCarTweet(WebJSONMixin, Document):
  """Stores a HotCar Tweet"""
  tweet_id = LongField(primary_key = True, required=True, db_field='_id')
  acknowledged = BooleanField(default = False, db_field = 'ack')
  embed_html = StringField(required = True)
  text = StringField(required = True)
  time = DateTimeField(required = True)
  user = ReferenceField(HotCarTweeter, required = True, db_field = "user_id")
  handle = StringField(required = True)

  meta = {'collection' : 'hotcars_tweets'}
  web_json_fields = ['embed_html', 'text', 'time', 'user', 'handle']

  def update_handle(self):
    """
    Update the handle stored in the tweet from the user document.
    """
    user_doc = self.user
    if user_doc.handle:
      self.handle = user_doc.handle
    self.save()

class HotCarReport(WebJSONMixin, Document):
  """Information on a hot car parsed from a tweet.
  The tweet is given by tweet_id.
  """
  tweet = ReferenceField(HotCarTweet, db_field = "tweet_id", unique = True)
  car_number = IntField(required = True)
  color = StringField()
  time = DateTimeField(required = True)
  #tweet_id = IntField()
  
  text = StringField()
  handle = StringField()
  user_id = LongField()

  meta = {'collection' : 'hotcars',
          'indexes': [('car_number', '-time'),
                      ('tweet'),
                      ('handle', '-time')]}

  web_json_fields = ['car_number', 'color', 'time', 'tweet']

  @classmethod
  def reports_for_car(cls, car_number):
    reports = list(cls.objects(car_number = car_number).order_by('-time').select_related())
    return reports

  @classmethod
  def num_reports_for_car(cls, car_number):
    return len(cls.objects(car_number = car_number))

  def denormalize(self):
    tweet = self.tweet
    self.user_id = tweet.user.user_id
    self.text = tweet.text
    self.handle = tweet.user.handle
    self.save()

  @classmethod
  def iter_reports(cls):
    """
    Return a generator over all reports.
    Convert naive timestamps into utc time.
    """
    all_reports = cls.objects
    for rec in all_reports:
      rec.time = rec.time.replace(tzinfo=tzutc)
      yield rec

  @classmethod
  def get_car_to_reports(cls):
    all_reports = cls.iter_reports()
    car_to_reports = defaultdict(list)
    for doc in all_reports:
      car_to_reports[doc.car_number].append(doc)
    return dict(car_to_reports)



class CarsForbiddenByMention(Document):
  """Hot Cars which are temporarily forbidden to be submitted
  by tweets which mention MetroHotCars.
  """
  car_number = IntField(required = True, primary_key = True, unique = True)
  time = DateTimeField(required = True)

  @classmethod
  def get_forbidden_cars(cls):
    docs = cls.objects.select_related()
    return [d.car_number for d in docs]


  @classmethod
  def remove_stale_docs(cls, time_delta = None):
    if not time_delta:
      time_delta = timedelta(days = 2)
    cur_time = utcnow()
    stale_docs = cls.objects(time__lt = cur_time - time_delta)
    for r in stale_docs:
      r.delete()

  @classmethod
  def add(cls, car_number, time):
    """
    Add a document or update existing one.
    """

    try:

      doc = cls.objects(car_number = car_number).get()

    except DoesNotExist:

      doc = cls(car_number = car_number, time = time)

    doc.time = time
    doc.save()

    

class Temperature(WebJSONMixin, Document):
  """Daily Temperature"""
  date = DateTimeField(primary_key = True, required=True, db_field = '_id')
  max_temp = FloatField(required=True, db_field = 'maxTemp')

  meta = {'collection' : 'temperatures'}
  web_json_fields = ['date', 'max_temp']

  @classmethod
  def update_latest_temperatures(cls, wunderground_api):
    ZIP_CODE = '20009'
    temps = cls.objects.order_by('-date')
    today = date.today()
    yesterday = today - timedelta(days = 1)
    if temps.count() == 0:
      last_day = yesterday
    else:
      last_day = temps[0].date.date()

    num_days = (today - last_day).days
    for i in range(num_days):
      day = last_day + timedelta(days = i + 1)
      rec = wunderground_api.getHistory(day, ZIP_CODE, sleep=True)
      max_temp = rec['dailysummary'][0]['maxtempi']
      new_temp_record = cls(date = day, max_temp = max_temp)
      new_temp_record.save()


