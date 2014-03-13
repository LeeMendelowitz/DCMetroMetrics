#!/bin/bash

# Script for running gunicorn server on digital ocean.
ROOT=/home/lmendelo/dcmetrometrics
source $ROOT/env.sh
source $ROOT/python/virtenv/bin/activate
cd $ROOT/repo

# Run gunicorn
gunicorn -w 4 -k gevent dcmetrometrics.web.server:app