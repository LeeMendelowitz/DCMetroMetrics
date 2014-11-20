# Make a csv file of units that have been rehabbed
import test
from dcmetrometrics.common import dbGlobals
dbGlobals.connect()
from dcmetrometrics.eles import models
rehabs = list(models.UnitStatus.objects(symptom_category = "REHAB"))

# Some rehabs are short statuses. Filter those out.
rehabs = [r for r in rehabs if (r.metro_open_time is None) or (r.metro_open_time > 7*24*3600)]
colnames = ['unit_id', 'station_name', 'station_desc','esc_desc','unit_type', 'time', 'end_time', 'metro_open_time']

def make_d(r):
    return tuple([getattr(r, c) for c in colnames])

def performance_30d(u):
  """Get 30 performance"""
  cols = ['availability', 'broken_time_percentage', 'num_breaks', 'num_inspections']
  ps = u.performance_summary.thirty_day
  d = {k:getattr(ps, k) for k in cols}
  d['unit_id'] = u.unit_id
  d['station_desc'] = u.station_desc
  d['esc_desc'] = u.esc_desc
  d['station_name'] = u.station_name
  return d

def performance_all_time(u):
  """Get 30 performance"""
  cols = ['availability', 'broken_time_percentage', 'num_breaks', 'num_inspections']
  ps = u.performance_summary.all_time
  d = {k:getattr(ps, k) for k in cols}
  d['unit_id'] = u.unit_id
  d['station_desc'] = u.station_desc
  d['esc_desc'] = u.esc_desc
  d['station_name'] = u.station_name
  return d

rehabs_cur = [r for r in rehabs if r.end_time is None]
rehabs_past = [r for r in rehabs if r not in rehabs_cur]

def make_df(records):
  ds = [make_d(r) for r in records]
  df = pandas.DataFrame(ds)
  df.columns = colnames
  return df


import pandas

rehabs_cur_df = make_df(sorted(rehabs_cur, key = attrgetter('station_name')))
rehabs_past_df = make_df(sorted(rehabs_past, key = attrgetter('station_name')))

rehabs_cur_df.to_csv('rehabbed.cur.csv', index=False)
rehabs_past_df.to_csv('rehabbed.past.csv', index=False)

metro_forward_units = ['C04X01','C04X02', 'C04X03', "A03S01", "A03S02", "A03S03", 'C07S07', 'C07S08', 'C07S09',
'A06X01', 'A06X02']
metro_forward_units = ['%sESCALATOR'%u for u in metro_forward_units]
metro_forward_units = [models.Unit.objects(unit_id = uid).get() for uid in metro_forward_units]
all_statuses = [u.get_statuses() for u in metro_forward_units]

# Gather long outages from the escalators we are considering
from dcmetrometrics.eles.StatusGroup import StatusGroup, Outage
sg = [StatusGroup(s[::-1]) for s in all_statuses]
outages = [s.outageStatuses for s in sg]
all_outages = [o for ol in outages for o in ol]
long_outages = [o for o in all_outages if o.metroOpenTime > 30*3600]

for o in long_outages:
  unit_id = o.statuses[0].unit_id
  end_time = o.end_time
  days = o.absTime / 24.0/3600.0
  print unit_id, end_time, '%.2f days'%days


# Get silver line units.
all_units = list(models.Unit.objects)
silver_units = [u for u in all_units if 'N0' in u.station_code]
performance_df = pandas.DataFrame([performance_30d(u) for u in metro_forward_units])
performance_df.to_csv('metro_forward_thirty_day.csv', index = False)
silver_performance_df = pandas.DataFrame([performance_30d(u) for u in silver_units])
silver_performance_df.sort('broken_time_percentage', ascending = False, inplace = True)
all_units_performance_df = pandas.DataFrame([performance_30d(u) for u in all_units])
all_units_performance_df.sort('broken_time_percentage', ascending = False, inplace = True)
all_units_performance_df.to_csv('all_units_performance.csv', index = False)
