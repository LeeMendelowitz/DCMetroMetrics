#!/bin/bash
# Dump MongoDB collections as json files
import os, sys, subprocess

#mongoexport -host $OPENSHIFT_MONGODB_DB_HOST -d MetroEscalators -u $OPENSHIFT_MONGODB_DB_USERNAME -p $OPENSHIFT_MONGODB_DB_PASSWORD -c $name > $OPENSHIFT_DATA_DIR/mongoexport/$name.json

cmd = 'mongoexport -host {host} -d {db} -u {user} -p {password} -c {col}'

HOST = os.environ['OPENSHIFT_MONGODB_DB_HOST']
USER = os.environ['OPENSHIFT_MONGODB_DB_USERNAME']
PASS = os.environ['OPENSHIFT_MONGODB_DB_PASSWORD']
DATA_DIR = os.environ['OPENSHIFT_DATA_DIR']

def dump(collection):
    myCmd = cmd.format(host=HOST, db='MetroEscalators', user=USER, password=PASS, col=collection)
    outputDir = os.path.join(DATA_DIR, 'mongoexport')
    if not os.path.exists(outputDir):
        os.mkdir(outputDir)
    outFile = os.path.join(outputDir, '%s.json'%collection)
    output = open(outFile, 'w')
    print 'CMD: ', myCmd
    myCmd = myCmd.split()
    p = subprocess.call(myCmd, stdout=output)
    output.close()

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
    for c in collections:
        dump(c)

if __name__ == '__main__':
    run()
