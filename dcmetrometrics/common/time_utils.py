from dateutil.tz import tzutc
from datetime import datetime

def utcnow():
  return datetime.now(tzutc())
