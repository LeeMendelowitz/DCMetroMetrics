#!/usr/bin/env python
# Load the json data into the local MongoDB Database

import glob
import pymongo
from pymongo import MongoClient
import subprocess
import os, sys

curfile = os.path.abspath(__file__)
curdir = os.path.split(curfile)[0]
parentdir = os.path.split(curdir)[0]

REPO_DIR = parentdir
JSON_DIR = os.path.join(REPO_DIR, 'data', 'json')

c = MongoClient()
db = c.MetroEscalators

jsons = glob.glob('%s/*.json'%JSON_DIR)

def run():

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

if __name__ == '__main__':
    run()
