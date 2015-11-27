"""
SQL models for eles data using sqlalchemy
"""

from sqlalchemy import create_engine
from sqlalchemy import (Column, Integer, String, Binary, Boolean, Enum, DateTime,
  Date,
  Float, UniqueConstraint, Index, ForeignKey)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
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
