"""
Methods to convert an object to csv
"""
import datetime
from pandas import Series, DataFrame
import os
from .utils import mkdir_p
from datetime import timedelta
from collections import defaultdict

from ..eles.models import (Unit, UnitStatus, KeyStatuses, Station, DailyServiceReport, SystemServiceReport)
from ..hotcars.models import HotCarReport
from ..hotcars.models import (HotCarReport, Temperature)
from ..common.metroTimes import tzutc, isNaive, toUtc

def s(v):
  if v is None:
    return 'NA'
  return unicode(v)

def q(v):
  """Quote strings"""
  if v is None:
    return '"NA"'
  if isinstance(v, (unicode, str)):
    return u'"%s"'%v
  return unicode(v)

class DataWriter(object):
  """Write csv files
  """

  def __init__(self, basedir = None):
    self.basedir = os.path.abspath(basedir) if basedir else os.getcwd()

  
  def write_units(self):
    fields = Unit.data_fields

    # Create the directory if necessary
    outdir = os.path.join(self.basedir, 'download')
    mkdir_p(outdir)

    fname = 'units.csv'
    outpath = os.path.join(outdir, fname)

    with open(outpath, 'w') as fout:

      # Write Header
      fout.write(','.join(fields) + '\n')
      for unit in Unit.objects.no_cache():
        unit_data = unit.to_data_record()
        outs = ','.join(q(unit_data[k]) for k in fields) + '\n'
        fout.write(outs.encode('utf-8'))

  def write_hot_cars(self):
    fields = HotCarReport.data_fields

    # Create the directory if necessary
    outdir = os.path.join(self.basedir, 'download')
    mkdir_p(outdir)

    fname = 'hotcars.csv'
    outpath = os.path.join(outdir, fname)

    with open(outpath, 'w') as fout:

      # Write Header
      fout.write(','.join(fields) + '\n')

      for report in HotCarReport.objects.no_cache().order_by('time'):
        report = report.clean()
        report_data = report.to_data_record()
        df = DataFrame([report_data], columns = fields)
        df.to_csv(fout, index = False, header=False, encoding='utf-8') # let pandas do the escaping

  def write_unit_statuses(self):

    fields = UnitStatus.data_fields

    # Create the directory if necessary
    outdir = os.path.join(self.basedir, 'download')
    mkdir_p(outdir)

    fname = 'unit_statuses.csv'
    outpath = os.path.join(outdir, fname)

    with open(outpath, 'w') as fout:

      # Write Header
      fout.write(','.join(fields) + '\n')
      statuses = UnitStatus.objects.timeout(False).order_by('time').no_cache()
      for status in statuses:
        status.clean()
        status_data = status.to_data_record()
        outs = ','.join(q(status_data[k]) for k in fields) + '\n'
        fout.write(outs.encode('utf-8'))

      statuses._cursor.close()





