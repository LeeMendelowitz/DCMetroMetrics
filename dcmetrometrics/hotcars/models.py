"""
Models for HotCars app.
"""

from mongoengine import *
from ..common.WebJSONMixin import WebJSONMixin

class HotCarAppState(Document):
  id = IntField(required=True, default = 1, db_field = '_id', primary_key=True)
  lastMentionsCheckTime = DateTimeField(required=True)
  lastMentionsTweetId = LongField()
  lastRunTime = DateTimeField()
  lastSelfTweetId = LongField()
  lastTweetId = LongField()

  meta = {'collection' : 'hotcars_appstate'}

  def __init__(self, *args, **kwargs):
    kwargs['id'] = 1
    super(self, HotCarAppState).__init__(*args, **kwargs)



class HotCarTweeter(WebJSONMixin, Document):
  """Information on a Hot Car Tweeter"""
  user_id = LongField(primary_key = True, required=True, db_field='_id')
  handle = StringField(required = True)

  meta = {'collection' : 'hotcars_tweeters'}
  web_json_fields = ['id', 'handle']


class HotCarTweet(WebJSONMixin, Document):
  """Stores a HotCar Tweet"""
  tweet_id = LongField(primary_key = True, required=True, db_field='_id')
  acknowledged = BooleanField(default = False, db_field = 'ack')
  embed_html = StringField(required = True)
  text = StringField(required = True)
  time = DateTimeField(required = True)
  user_id = ReferenceField(HotCarTweeter, required = True, db_field = "user_id")
  handle = StringField(required = True)

  meta = {'collection' : 'hotcars_tweets'}
  web_json_fields = ['embed_html', 'text', 'time', 'user_id', 'handle']


class HotCarReport(WebJSONMixin, Document):
  """Information on a hot car parsed from a tweet.
  The tweet is given by tweet_id.
  """
  car_number = IntField(required = True)
  color = StringField()
  time = DateTimeField(required = True)
  #tweet_id = IntField()
  tweet = ReferenceField(HotCarTweet, db_field = "tweet_id")

  meta = {'collection' : 'hotcars',
          'indexes': [('car_number', '-time')]}

  web_json_fields = ['car_number', 'color', 'time', 'tweet']

  @classmethod
  def reports_for_car(cls, car_number):
    reports = list(cls.objects(car_number = car_number).order_by('-time').select_related())
    return reports
    

class Temperature(WebJSONMixin, Document):
  """Daily Temperature"""
  date = DateTimeField(primary_key = True, required=True, db_field = '_id')
  max_temp = FloatField(required=True, db_field = 'maxTemp')

  meta = {'collection' : 'temperatures'}
  web_json_fields = ['date', 'max_temp']
