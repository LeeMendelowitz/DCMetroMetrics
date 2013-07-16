#!/usr/bin/env python
# Load the json data into the local MongoDB Database

import glob
import pymongo
from pymongo import MongoClient
import subprocess
import os

c = MongoClient()
db = c.MetroEscalators

jsons = glob.glob('*.json')

for fname in jsons:
    base, ext = os.path.splitext(fname)
    collection = base
    print '*'*50
    print 'Dropping collection %s'%collection
    db[collection].drop()
    print 'Importing json %s'%fname
    cmd = 'mongoimport -d MetroEscalators -c {collection} {fname}'
    cmd = cmd.format(collection=collection, fname=fname)
    subprocess.call(cmd, shell=True)
