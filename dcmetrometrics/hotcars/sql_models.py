"""
SQL models for hotcars data using sqlalchemy
"""

from sqlalchemy import create_engine
from sqlalchemy import (Column, Integer, String, Binary, Boolean, Enum, DateTime,
  Date,
  Float, UniqueConstraint, Index, ForeignKey)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy.dialects import mysql

import sys, os
import uuid, hashlib
from datetime import datetime
import pandas as pd
import json

Base = declarative_base()

##############################################################################
# Utility Class
#
class DocMixin(object):

  def update_from_dict(self, d):
    for k, v in d.iteritems():
      setattr(self, k, v if pd.notnull(v) else None)

  @classmethod
  def create_from_dict(cls, d):
    ret = cls()
    ret.update_from_dict(d)
    return ret

class JSONMixin(object):
  """Return Model object as a dict or json.
  We don't follow any complex relationships or anything fancy.
  """

  def as_dict(self):
    keys = getattr(self, '__json_keys__', None)
    if not keys:
      keys = self.__table__.columns.keys()

    ret = { k : getattr(self, k, None) for k in keys }
    return ret

  def as_json(self):
    return json.dumps(self.as_dict())

###############################################################

class Temperature(JSONMixin, DocMixin, Base):
  """Temperature"""

  __tablename__ = 'temperatures'

  date = Column(Date, primary_key = True)
  max_temp = Column(Float)


class HotCarTweet(JSONMixin, DocMixin, Base):

  __tablename__ = 'hot_car_tweets'

  tweet_id = Column(mysql.BIGINT, primary_key = True, autoincrement = False)
  ack = Column(Boolean, default = False)
  embed_html = Column(String(1024))
  text = Column(String(180))
  time = Column(DateTime)
  user_id = Column(mysql.BIGINT, ForeignKey('hot_car_tweeters.user_id', onupdate="CASCADE", ondelete="CASCADE"))
  user = relationship("HotCarTweeter", back_populates="tweets")
  reports = relationship("HotCarReport", back_populates="tweet")


class HotCarTweeter(JSONMixin, DocMixin, Base):

  __tablename__ = 'hot_car_tweeters'

  user_id = Column(mysql.BIGINT, primary_key = True, autoincrement = False)
  handle = Column(String(255))
  tweets = relationship("HotCarTweet", back_populates="user")


class HotCarReport(JSONMixin, DocMixin, Base):

  __tablename__ = 'hot_car_reports'
  
  pk = Column(mysql.BIGINT, primary_key = True)
  tweet_pk = Column(mysql.BIGINT, ForeignKey('hot_car_tweets.tweet_id', onupdate="CASCADE", ondelete="CASCADE"))
  color = Column(String(16))
  car_number = Column(Integer, index = True, nullable = False)
  tweet = relationship("HotCarTweet", back_populates="reports")

