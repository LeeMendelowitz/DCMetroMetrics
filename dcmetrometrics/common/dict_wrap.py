"""
Dict Wrap takes a dictionary with string keys
and creates an instance of an object with those attributes
"""
from itertools import izip


class DictWrap(object):

    def __init__(self, d):
        for k, val in d.iteritems():
            setattr(self, str(k), val)

        self.myKeys = d.keys()

    def keys(self):
        return self.myKeys
    def iterkeys(self):
        return (k for k in self.myKeys)
    def values(self):
        return [getattr(self, k) for k in self.myKeys]
    def itervalues(self):
        return (v for v in self.values())
    def items(self):
        return zip(self.keys(), self.values())
    def iteritems(self):
        return ((k,v) for k,v in izip(self.keys(), self.values()))
