#!/bin/bash
# Delete pickle data from greater than 24 hours ago
find $OPENSHIFT_DATA_DIR -name "*.pickle" -mtime +0 | xargs -I {} rm {}
#find $OPENSHIFT_DATA_DIR -name "*.pickle" -mtime +0
