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
parser.add_argument('--db', default="MetroEscalators", help='The database to use.')
parser.add_argument('--zip', default="./DCMetroMetricsData", help='The zip file to use')

c = MongoClient()


def run():
    args = parser.parse_args()

    ZIP = args.zip

    if not os.path.exists(ZIP):
        raise RuntimeError("Could not find zip file: %s"%ZIP)

    UNZIPPED_DIR = os.path.abspath('./DCMetroMetricsData')

    # Download the latest data zip file
    # cmd = "curl http://www.dcmetrometrics.com/data/{ZIP} > {ZIP}".format(ZIP=ZIP)
    # call(cmd, shell=True)

    if os.path.exists(UNZIPPED_DIR):
        shutil.rmtree(UNZIPPED_DIR)

    # Unzip
    cmd = "unzip %s"%ZIP
    call(cmd, shell=True)

    db = c[args.db]

    jsons = glob.glob('%s/*.json'%UNZIPPED_DIR)
    print 'Json Directory: %s'%UNZIPPED_DIR
    print 'Found %i jsons'%len(jsons)
    for j in jsons:
        path, name = os.path.split(j)
        print ' - %s'%(name)

    for j in jsons:
        path, fname = os.path.split(j)
        base, ext = os.path.splitext(fname)
        collection = base
        print '*'*50
        print 'Dropping collection %s'%collection
        db[collection].drop()
        print 'Importing json %s into collection %s'%(j, collection)
        cmd = 'mongoimport -d {db} -c {collection} {fname}'
        cmd = cmd.format(db = args.db, collection=collection, fname=j)
        call(cmd, shell=True)

if __name__ == '__main__':
    run()
