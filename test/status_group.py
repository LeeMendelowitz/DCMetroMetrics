import unittest
import setup

from dcmetrometrics.eles import models
from dcmetrometrics.eles.StatusGroup import StatusGroup
from dcmetrometrics.common.metroTimes import utcnow, nytz
from datetime import timedelta, datetime

class TestOutageDays(unittest.TestCase):

  def setUp(self):

      t1 = datetime(2015, 2, 16, 22, tzinfo = nytz)

      # Outage does not cover the 17th since resolved before system open
      t2 = datetime(2015, 2, 17, 3, tzinfo = nytz) 
      t3 = datetime(2015, 2, 21, 4, tzinfo = nytz) # This covers 20 and 21

      s1 = models.UnitStatus(time = t1, end_time = t2, symptom_category = "BROKEN")
      s2 = models.UnitStatus(time = t2, end_time = t3, symptom_category = "ON" )
      s3 = models.UnitStatus(time = t3, end_time = None, symptom_category = "BROKEN")

      self.statuses = [s1, s2, s3]
      self.start_time = t1

  def test_end_time_1(self):
    end_time = datetime(2015, 2, 22, 10, tzinfo = nytz)
    sg = StatusGroup(self.statuses, self.start_time,  end_time)
    bd = sg.break_days
    self.assertEqual(len(sg.break_days), 4)

  def test_end_time_2(self):
    end_time = datetime(2015, 2, 22, 4, tzinfo = nytz)
    sg = StatusGroup(self.statuses, self.start_time, end_time)
    bd = sg.break_days
    self.assertEqual(len(sg.break_days), 3)

class TestTrimming(unittest.TestCase):

  def setUp(self):

    t1 = datetime(2015, 2, 16, 22, tzinfo = nytz)

    # Outage does not cover the 17th since resolved before system open
    t2 = datetime(2015, 2, 17, 3, tzinfo = nytz) 
    t3 = datetime(2015, 2, 21, 4, tzinfo = nytz) # This covers 20 and 21

    s1 = models.UnitStatus(time = t1, end_time = t2, symptom_category = "BROKEN")
    s2 = models.UnitStatus(time = t2, end_time = t3, symptom_category = "ON" )
    s3 = models.UnitStatus(time = t3, end_time = None, symptom_category = "BROKEN")

    self.statuses = [s1, s2, s3]
    self.start_time = t1

  def test_trim_1(self):
    start_time = datetime(2015, 2, 17, 1, tzinfo = nytz)
    end_time = datetime(2015, 2, 25, 4, tzinfo = nytz)
    statuses = self.statuses
    sg = StatusGroup(statuses, start_time, end_time)
    self.assertEqual(sg.statuses_trimmed[0].time, start_time)
    self.assertEqual(sg.statuses_trimmed[-1].end_time, end_time)

  def test_trim_2(self):
    start_time = datetime(2015, 2, 17, 1, tzinfo = nytz)
    end_time = datetime(2015, 2, 21, 2, tzinfo = nytz)
    statuses = self.statuses
    sg = StatusGroup(statuses, start_time, end_time)
    self.assertEqual(sg.statuses_trimmed[0].time, start_time)
    self.assertEqual(sg.statuses_trimmed[-1].end_time, end_time)



if __name__ == '__main__':
  unittest.main()