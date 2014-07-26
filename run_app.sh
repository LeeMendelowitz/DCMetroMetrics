d#!/bin/bash

# Script for running the dcmetrometrics worker app on digital ocean
ROOT=/home/lmendelo/dcmetrometrics
source $ROOT/env.sh
source $ROOT/python/virtenv/bin/activate
cd $ROOT/repo

# Run gunicorn
python app.py