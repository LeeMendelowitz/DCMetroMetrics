"""
Script to perform database migrations for the ELES App.

Script to denormalize the database by adding fields to the unit status records.

This should be imported as a module and not run directly.
"""

from . import utils
utils.fixSysPath()

import sys
from datetime import datetime

from dcmetrometrics.common.dbGlobals import G
from dcmetrometrics.hotcars.models import (HotCarAppState, HotCarTweeter, HotCarTweet,
  HotCarReport, CarsForbiddenByMention, Temperature)
from dcmetrometrics.hotcars.twitter_api import TwitterError, getTwitterAPI
from datetime import timedelta
import logging

from dcmetrometrics.common.JSONifier import JSONWriter
from dcmetrometrics.common.globals import WWW_DIR

##########################
def update_twitter_handles():
    """
    For each twitter user, look up the user and the handle.
    Save the twitter user to the hotcars_tweeters collection.
    """

    user_ids = set(t.user_id for t in HotCarTweeter.objects)
    user_ids = list(user_ids)

    print "Have %i users"%len(user_ids)

    # Make requests in batch of 100
    def gen_batches(d):
      i = 0
      n = 100
      ret = d[i:i+n]
      while ret:
        yield ret
        i = i + n
        ret = d[i:i+n]

    T = getTwitterAPI()

    for i, user_id_batch in enumerate(gen_batches(user_ids)):

      print "Querying Twitter with batch %i"%i

      try:

        user_info = T.UsersLookup(user_id = user_id_batch)

        for user in user_info:
          user_id = user.id
          handle = user.screen_name
          HotCarTweeter.update(user_id, handle)

      except TwitterError as e:
        print("Caught twitter error:\n%s"%str(e))

    denormalize_reports()

def denormalize_reports():
  """
  Denormalize all hot car report docs by setting the
  user_id field, text field, and handle field.

  """
  for doc in HotCarReport.iter_reports():
    doc.denormalize()

def write_json():
  jwriter = JSONWriter(WWW_DIR)
  jwriter.write_hotcars()
  jwriter.write_hotcars_by_day()