"""Utilities for maintaining SQLAlchemy db connections and sessions
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class DBManager(object):

  def __init__(self, username, password, host, database, port = 3306):

    self.username = username
    self.password = password
    self.host = host
    self.port = port

    connect_str = "mysql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}".format(USER=username, PASSWORD=password,
      HOST=host, PORT=port, DATABASE=database)

    self.my_engine = create_engine(connect_str, pool_recycle=3600)

    self.sessionmaker = sessionmaker(bind=self.my_engine)

  @property
  def engine(self):
    return self.my_engine

  @property
  def session(self):
    return self.sessionmaker()


_dcmm_db = None
def get_dcmm_db():
  global _dcmm_db
  if _dcmm_db is None:
    user = os.environ["DCMM_DB_USERNAME"]
    password = os.environ["DCMM_DB_PASSWORD"]
    host = os.environ["DCMM_DB_HOST"]
    database = "dcmm"
    _dcmm_db = DBManager(user, password, host, database)
  return _dcmm_db

_dcmm_db_test = None
def get_dcmm_test_db():
  global _dcmm_db_test
  if _dcmm_db_test is None:
    user = os.environ["DCMM_DB_USERNAME"]
    password = os.environ["DCMM_DB_PASSWORD"]
    host = os.environ["DCMM_DB_HOST"]
    database = "dcmm_test"
    _dcmm_db_test = DBManager(user, password, host, database)
  return _dcmm_db_test
