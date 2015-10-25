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


_trackman_www_db = None
def get_trackman_www_db():
  global _trackman_www_db
  if _trackman_www_db is None:
    user = os.environ["TM_WWW_DB_USERNAME"]
    password = os.environ["TM_WWW_DB_PASSWORD"]
    host = os.environ["TM_WWW_DB_HOST"]
    database = "www_trackman"
    _trackman_www_db = DBManager(user, password, host, database)
  return _trackman_www_db

_trackman_www_db_test = None
def get_trackman_www_test_db():
  global _trackman_www_db_test
  if _trackman_www_db_test is None:
    user = os.environ["TM_WWW_DB_USERNAME"]
    password = os.environ["TM_WWW_DB_PASSWORD"]
    host = os.environ["TM_WWW_DB_HOST"]
    database = "www_trackman_test"
    _trackman_www_db_test = DBManager(user, password, host, database)
  return _trackman_www_db_test
