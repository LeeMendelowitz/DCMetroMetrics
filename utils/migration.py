"""Migrate the database to the new version. 8/11/2014"""

import test
from dcmetrometrics.common import dbGlobals
dbGlobals.connect()

from utils import denormalize_db
denormalize_db.update_symptom_codes()
denormalize_db.update_unit_statuses()
denormalize_db.denormalize_unit_statuses()
denormalize_db.recompute_key_statuses()


# Finally, we need to create the stations in the database
denormalize_db.add_station_docs()