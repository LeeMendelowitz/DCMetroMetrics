"""
SQL models for eles data using sqlalchemy
"""

from sqlalchemy import create_engine
from sqlalchemy import (Column, Integer, String, Binary, Boolean, Enum, DateTime,
  Float, UniqueConstraint, Index, ForeignKey)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
import sys, os
import uuid, hashlib
from datetime import datetime
import pandas as pd
import json


Base = declarative_base()

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
class Station(JSONMixin, DocMixin, Base):
  """Team data from the MLBAM teamhistory table"""

  __tablename__ = 'station'

  code = Column(String(3), primary_key = True)
  station_group = Column(Integer, ForeignKey('station_group.pk'))

  # Define what lines the station belongs to
  red = Column(Boolean, nullable = False, default = False)
  orange = Column(Boolean, nullable = False, default = False)
  yellow = Column(Boolean, nullable = False, default = False)
  green = Column(Boolean, nullable = False, default = False)
  blue = Column(Boolean, nullable = False, default = False)
  silver = Column(Boolean, nullable = False, default = False)


class StationGroup(JSONMixin, DocMixin, Base):

  __tablename__ = 'station_group'

  pk = Column(Integer, primary_key = True, autoincrement = True)
  long_name = Column(String(255))
  medium_name = Column(String(255))
  short_name = Column(String(255))
  stations = relationship("Station")