"""
Definition of the Interval protocol.
Utilities to take union and intersection of intervals.
"""


class Interval(object):
    """
    Representation of an interval
    > I = Interval(0, 10)
    """
    def __init__(self, start, end):
        assert(start <= end)
        self.start = start
        self.end = end

    def length(self):
        return self.end - self.start

    def __lt__(self, other):
        print 'calling __lt__'
        return self.start < other.start

    def __eq__(self, other):
        print 'calling __eq__'
        return self.start == other.start and self.end == other.end

    def __str__(self):
        return '(%s, %s)'%(str(self.start), str(self.end))

    def __repr__(self):
        return 'Interval%s'%str(self)

def pairwise_overlaps(i1, i2):
    """
    Check if two intervals have an overlap.
    Treat the intervals as open.
    """
    return not ((i1.end <= i2.start) or (i2.end <= i1.start))

def pairwise_union(i1, i2):
    assert(type(i1) == type(i2))
    T = type(i1)
    if not pairwise_overlaps(i1, i2):
        return [i1, i2]
    start = min(i1.start, i2.start)
    end = max(i1.end, i2.end)
    return T(start, end)

def pairwise_intersect(i1, i2):
    assert(type(i1) == type(i2))
    T = type(i1)
    if not pairwise_overlaps(i1, i2):
        return []
    start = max(i1.start, i2.start)
    end = min(i1.end, i2.end)
    assert(start <= end)
    return T(start, end)

def union(intervals):
    """
    Take the union of a list of Intervals or 
    a list of Interval like objects.
    """
    intervals = sorted(intervals)
    done = False
    startInd = 0
    while not done:
        leftI = intervals[startInd:-1]
        rightI = intervals[startInd+1:]
        foundOverlap = False
        for ind, (l, r) in enumerate(zip(leftI, rightI)):
            if pairwise_overlaps(l, r):
                foundOverlap = True
                newInterval = pairwise_union(l,r)
                intervals = intervals[0:startInd+ind] + [newInterval] + intervals[startInd+ind+2:] 
                startInd = startInd + ind
                break
        done = not foundOverlap
    return intervals

def intersect(intervals):
    """
    Take the intersection of a list of Intervals or
    a list of Interval like objects.
    """
    if not intervals:
        return None
    if len(intervals) == 1:
        return intervals
    intervals = sorted(intervals)
    I = intervals[0]
    for i in intervals[1:]:
        I = I._intersect(i)
        if I is None:
            break
    return I
