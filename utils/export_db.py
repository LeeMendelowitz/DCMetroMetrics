#!/usr/bin/env python
"""
Dump MongoDB collections as json files.
Create a DCMetroMetricsData.zip file.
The zip file is available for download via URL:
http://www.dcmetrometrics.com/data/DCMetroMetricsData.zip
"""
import os, sys, subprocess, shutil
from glob import glob

def p(msg):
    sys.stdout.write(msg + '\n')
    sys.stdout.flush()

cmd = 'mongoexport -host {host} -d {db} -c {col}'

HOST = os.environ['MONGODB_HOST']
DATA_DIR = os.environ['DATA_DIR']
OUTPUT_DIR_BASE = os.path.join(DATA_DIR, 'mongoexport')
JSON_DIR_NAME = 'DCMetroMetricsData'
JSON_DIR = os.path.join(OUTPUT_DIR_BASE, JSON_DIR_NAME)
SHARED_DATA_DIR = os.path.join(DATA_DIR, 'shared')

# Making output directories if they do not exist
def make_dir(path):
    if not os.path.exists(path):
        os.mkdir(path)

make_dir(OUTPUT_DIR_BASE)
make_dir(JSON_DIR)
make_dir(SHARED_DATA_DIR)

def dump(collection):
    """
    dump a MongoDB collection into a .json file using mongoexport.
    """

    myCmd = cmd.format(host=HOST, db='MetroEscalators', col=collection)

    outFile = '%s.json'%collection
    outFile = os.path.join(JSON_DIR, outFile)
    output = open(outFile, 'w')

    # Run MongoExport
    #print 'CMD: ', myCmd
    p('Exporing collection %s...'%collection)
    myCmd = myCmd.split()
    subprocess.call(myCmd, stdout=output)
    output.close()
    p('DONE.')

collections = [
'elevator_appstate',
'elevator_tweet_outbox',
'escalator_appstate',
'escalator_statuses',
'escalator_tweet_outbox',
'escalators',
'hotcars',
'hotcars_appstate',
'hotcars_forbidden_by_mention',
'hotcars_manual_tweets',
'hotcars_tweeters',
'hotcars_tweets',
'symptom_codes',
'webpages',
'temperatures',
]


def run():

    # Remove old json and zip files
    os.chdir(OUTPUT_DIR_BASE)
    jsonPattern = os.path.join(JSON_DIR, '*.json')
    oldFiles = glob('*.json')
    zipPattern = os.path.join(OUTPUT_DIR_BASE, '*.zip')
    oldFiles.extend(glob(zipPattern))
    for f in oldFiles:
        os.unlink(f)

    # Create new json files
    for c in collections:
        dump(c)

    # Zip the json files
    jsonFiles = ('%s.json'%c for c in collections)
    jsonFiles = [os.path.join(JSON_DIR_NAME, f) for f in jsonFiles]
    cmd = ['zip', JSON_DIR_NAME]
    cmd.extend(jsonFiles)
    subprocess.call(cmd)

    outputZipFile = '%s.zip'%JSON_DIR_NAME

    # Copy the zip file into the public data directory
    # By placing in that directory, it is accessible thru:
    # http://www.dcmetrometrics.com/data/<outputZipFile>
    shutil.copy(outputZipFile, SHARED_DATA_DIR)

if __name__ == '__main__':
    run()
