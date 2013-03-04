#!/bin/bash
#find $OPENSHIFT_DATA_DIR -name '*.pickle' -ctime +1d  | xargs -I {} rm {}
find $OPENSHIFT_DATA_DIR -name '*.pickle' -ctime +1d 
