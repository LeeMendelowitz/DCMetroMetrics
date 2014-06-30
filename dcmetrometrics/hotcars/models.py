"""
Models for HotCars app.
"""

from mongoengine import *

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

class HotCarReport(Document):
  car_number = IntField(required = True)
  color = StringField(required = True)
  time = DateTimeField(required = True)
  tweet_id = IntField()

  meta = {'collection' : 'hotcars',
          'indexes': [('car_number', '-time')]}

class HotCarTweeter(Document):
  id = LongField(primary_key = True, required=True, db_field='_id')
  handle = StringField(required = True)

  meta = {'collection' : 'hotcars_tweeters'}

class HotCarTweet(Document):
  id = LongField(primary_key = True, required=True, db_field='_id')
  acknowledged = BooleanField(default = False, db_field = 'ack')
  embed_html = StringField(required = True)
  text = StringField(required = True)
  time = DateTimeField(required = True)
  user_id = ReferenceField(HotCarTweeter, required = True)
  handle = StringField(required = True)

  meta = {'collection' : 'hotcars_tweets'}

class Temperature(Document):
  id = DateTimeField(primary_key = True, required=True, db_field = '_id')
  max_temp = FloatField(required=True, db_field = 'maxTemp')

  meta = {'collection' : 'temperatures'}
