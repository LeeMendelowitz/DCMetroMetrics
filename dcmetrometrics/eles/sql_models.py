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

from .defs import symptomToCategory, SYMPTOM_CHOICES

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
class Station(JSONMixin, DocMixin, Base):
  """A Metrorail platform."""

  __tablename__ = 'station'

  code = Column(String(3), primary_key = True)
  station_group_id = Column(Integer, ForeignKey('station_group.pk'))

  # Define what lines the station belongs to
  red = Column(Boolean, nullable = False, default = False)
  orange = Column(Boolean, nullable = False, default = False)
  yellow = Column(Boolean, nullable = False, default = False)
  green = Column(Boolean, nullable = False, default = False)
  blue = Column(Boolean, nullable = False, default = False)
  silver = Column(Boolean, nullable = False, default = False)

  units = relationship("Unit", backref="station")

class StationGroup(JSONMixin, DocMixin, Base):
  """A group of Metrorail platforms"""

  __tablename__ = 'station_group'

  pk = Column(Integer, primary_key = True, autoincrement = True)
  long_name = Column(String(255))
  medium_name = Column(String(255))
  short_name = Column(String(255))

  stations = relationship("Station", backref="station_group")


class Unit(JSONMixin, DocMixin, Base):
  """
  An escalator or an elevator.
  """
  __tablename__ = 'unit'

  id = Column(String(31), primary_key = True)
  station_code = Column(String(3), ForeignKey('station.code'))
  station_name = Column(String(255))
  station_desc = Column(String(255))
  unit_desc = Column(String(255))
  unit_type = Column(Enum('ESCALATOR', 'ELEVATOR'))
  statuses = relationship("UnitStatus", backref="unit")

  # TODO:
  # key_statuses = EmbeddedDocumentField(KeyStatuses)
  # performance_summary = EmbeddedDocumentField(UnitPerformanceSummary)

class UnitStatus(JSONMixin, DocMixin, Base):
  """
  Escalator or elevator status.
  """
  __tablename__ = 'unit_status'
  pk = Column(Integer, primary_key = True)
  unit_id = Column(String(31), ForeignKey("unit.id"))
  time = Column(DateTime, nullable = False)
  end_time = Column(DateTime, nullable = False)
  metro_open_time = Column(Float)
  symptom = Column(Integer, ForeignKey("symptom_code.pk"), nullable = False)
  tick_delta = Column(Float, nullable = False, default = 0.0)
  update_type = Column(Enum('Off', 'On', 'Break', 'Fix', 'Update'))


class SymptomCode(JSONMixin, DocMixin, Base):
  """
  The different states an Unit can be in.
  """

  __tablename__ = "symptom_code"
  pk = Column(Integer, primary_key = True)
  description = Column(String(63), nullable = False, unique = True)
  category = Column(Enum(*SYMPTOM_CHOICES), nullable = False)
