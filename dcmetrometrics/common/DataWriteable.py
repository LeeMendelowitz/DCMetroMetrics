from datetime import date, datetime


def convert(k, v):
  """Convert a k,v pair into a dictionary.
  If v is a dictionary, it will be flattened
  """
  if isinstance(v, (int, float, str, unicode)) or v is None:
    return {k: v}
  elif isinstance(v, long):
    return {k: unicode(v)} # Return as unicode to prevent loss of precision
  elif isinstance(v, (date, datetime)):
    return {k: v.isoformat()}
  elif isinstance(v, dict):
    ret = {}
    for k2, v2 in v.iteritems():
      k3 = '%s_%s'%(k, k2) # flatten the keys
      ret.update(convert(k3, v2))
    return ret
  raise TypeError("Cannot convert value of %s"%type(v))

class DataWriteable(object):
  """This will flatten objects into a single dictionary
  """

  def to_data_record(self, keep_na = True):

    fields = getattr(self, 'data_fields', [])
    ret = {}

    for k in fields:

      v = getattr(self, k, None)

      if keep_na:
        ret.update(convert(k, v))
      elif v is not None:
        ret.update(convert(k, v))

    return ret