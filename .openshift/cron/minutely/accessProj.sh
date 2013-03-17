#!/bin/bash
URL=https://metroescalators-lmm.rhcloud.com/
cd $OPENSHIFT_REPOT_DIR/data
wget -O temp.html $URL
rm temp.html
