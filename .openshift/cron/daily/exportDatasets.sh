#!/bin/bash
# Export datasets as .json and .csv files for the
# DC Metro Metrics data webpage.
python $OPENSHIFT_REPO_DIR/utils/exportData.py
