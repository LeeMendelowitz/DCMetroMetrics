#!/usr/bin/env python
"""
Downloads the latest DC Metro Metrics data from www.DCMetroMetrics.com
Loads the data into the local MongoDB Database
An instance of mongod must be running.
"""

from pymongo import MongoClient
import os, sys, shutil, glob, argparse
from subprocess import call

parser = argparse.ArgumentParser(description="Import DCMetroMetrics data into MongoDB")

c = MongoClient()
db = c.MetroEscalators

def run():
    args = parser.parse_args()

    ZIP = 'DCMetroMetricsData.zip'
    UNZIPPED_DIR = os.path.abspath('./DCMetroMetricsData')

    # Download the latest data zip file
    cmd = "curl http://www.dcmetrometrics.com/data/{ZIP} > {ZIP}".format(ZIP=ZIP)
    call(cmd, shell=True)

    if os.path.exists(UNZIPPED_DIR):
        shutil.rmtree(UNZIPPED_DIR)

    # Unzip
    cmd = "unzip %s"%ZIP
    call(cmd, shell=True)


    jsons = glob.glob('%s/*.json'%UNZIPPED_DIR)
    print 'Json Directory: %s'%UNZIPPED_DIR
    print 'Found %i jsons'%len(jsons)
    for j in jsons:
        path, name = os.path.split(j)
        print ' - %s'%(name)

    for fname in jsons:
        base, ext = os.path.splitext(fname)
        collection = base
        print '*'*50
        print 'Dropping collection %s'%collection
        db[collection].drop()
        print 'Importing json %s'%fname
        cmd = 'mongoimport -d MetroEscalators -c {collection} {fname}'
        cmd = cmd.format(collection=collection, fname=fname)
        call(cmd, shell=True)

if __name__ == '__main__':
    run()
