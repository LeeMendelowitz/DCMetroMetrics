"""
Methods to convert an oect to json for the web.
"""
from json import JSONEncoder, dumps
import datetime
import os
from .utils import mkdir_p
from datetime import timedelta
from collections import defaultdict


from ..eles.models import (Unit, UnitStatus, KeyStatuses, Station)
from ..hotcars.models import (HotCarReport, Temperature)
from ..common.WebJSONMixin import WebJSONMixin
from ..common.metroTimes import tzutc, isNaive, toUtc

class WebJSONEncoder(JSONEncoder):
  """JSON Encoder for DC Metro Metrics data types.
  """

  def default(self, o):

    # Convert dates to string
    if isinstance(o, datetime.datetime) or \
       isinstance(o, datetime.date):

      # If the datetime is naive, assume it is in UTC timezone.
      if isinstance(o, datetime.datetime) and isNaive(o):
        o = toUtc(o, allow_naive = True)

      return o.isoformat()

    # Convert ELES models
    elif isinstance(o, (WebJSONMixin)):
      return o.to_web_json()

    # Let the base class default method raise the TypeError
    return JSONEncoder.default(self, o)


class JSONWriter(object):
  """Write Unit and Station JSON static files.
  """

  def __init__(self, basedir = None):
    self.basedir = os.path.abspath(basedir) if basedir else os.getcwd()

  def write_unit(self, unit):

    # Get the statuses for the unit
    statuses = unit.get_statuses()

    # Get the key statuses
    #key_statuses = unit.get_key_statuses()

    performance_summary = unit.performance_summary

    data = {'unit' : unit,
            #'key_statuses' : key_statuses, #Redundant, already included in unit.
            'statuses' : statuses,
            'performance_summary' : performance_summary}
    
    jdata = dumps(data, cls = WebJSONEncoder)

    # Create the directory if necessary
    outdir = os.path.join(self.basedir, 'json', 'units')
    mkdir_p(outdir)

    fname = '%s.json'%(unit.unit_id)
    outpath = os.path.join(outdir, fname)

    with open(outpath, 'w') as fout:
      fout.write(jdata)

  def write_station_directory(self):

    sd = Station.get_station_directory()
    jdata = dumps(sd, cls = WebJSONEncoder)

    # Create the directory if necessary
    outdir = os.path.join(self.basedir, 'json')
    mkdir_p(outdir)

    fname = '%s.json'%('station_directory')
    outpath = os.path.join(outdir, fname)

    with open(outpath, 'w') as fout:
      fout.write(jdata)


  def write_recent_updates(self):
    """
    Write a list of recent status changes
    """

    recent = list(UnitStatus.objects.order_by('-time')[:20])
    jdata = dumps(recent, cls = WebJSONEncoder)

    # Create the directory if necessary
    outdir = os.path.join(self.basedir, 'json')
    mkdir_p(outdir)

    fname = 'recent_updates.json'
    outpath = os.path.join(outdir, fname)

    with open(outpath, 'w') as fout:
      fout.write(jdata)

  def write_hotcars(self):
    """
    Write all hot car reports
    """
    recent = list(HotCarReport.objects.order_by('-time').select_related())
    jdata = dumps(recent, cls = WebJSONEncoder)

    # Create the directory if necessary
    outdir = os.path.join(self.basedir, 'json')
    mkdir_p(outdir)

    fname = 'hotcar_reports.json'
    outpath = os.path.join(outdir, fname)

    with open(outpath, 'w') as fout:
      fout.write(jdata)

  def write_hotcars_by_day(self):
    """
    Write hot car counts by day.
    """
    all_reports = list(HotCarReport.objects.order_by('time').select_related())
    day_to_count = defaultdict(int)

    for r in all_reports:
      r.time.replace(tzinfo=tzutc)
      day_to_count[r.time.date()] += 1

    day_to_temp = dict((t.date.date(), t.max_temp) for t in Temperature.objects.order_by('date'))

    # Create time series for both temperate and counts
    first_day = all_reports[0].time.date()
    last_day = all_reports[-1].time.date()

    def gen_days(s, e):
      d = s
      while d < e:
        yield d
        d = d + timedelta(days = 1)

    days = gen_days(first_day, last_day + timedelta(days = 1))
    daily_series = [{'day': d,
                     'count' : day_to_count.get(d, 0),
                     'temp' : day_to_temp.get(d, None)} for d in days]
    # temp_series = [{'day':t.date.date(), 'temp': t.max_temp} for t in Temperature.objects.order_by('date')]

    ret = {'daily_series' : daily_series}

    jdata = dumps(ret, cls = WebJSONEncoder)

    # Create the directory if necessary
    outdir = os.path.join(self.basedir, 'json')
    mkdir_p(outdir)

    fname = 'hotcars_by_day.json'
    outpath = os.path.join(outdir, fname)

    with open(outpath, 'w') as fout:
      fout.write(jdata)









